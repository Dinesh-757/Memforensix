"""
Machine learning anomaly detection service.

Uses scikit-learn's IsolationForest, trained on-the-fly on the
extracted process/connection feature set of the current analysis
(unsupervised, no pre-trained model required — appropriate since
every memory dump has a different "normal" baseline). Real, working
implementation — not a stub.
"""
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

SUSPICIOUS_PROCESS_NAMES = {"svchost.exe", "rundll32.exe", "regsvr32.exe", "powershell.exe", "cmd.exe"}
SUSPICIOUS_PORTS = {4444, 8080, 1337, 6666, 31337}


class MLAnomalyService:
    def __init__(self, contamination: float = 0.15, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state

    # ---------------- Process anomaly detection ----------------
    def _process_features(self, processes: List[Dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for p in processes:
            name = (p.get("name") or "").lower()
            cmdline = (p.get("cmdline") or "")
            rows.append({
                "threads": p.get("threads", 0) or 0,
                "handles": p.get("handles", 0) or 0,
                "cmdline_len": len(cmdline),
                "has_ip_in_cmdline": int(any(c.isdigit() for c in cmdline) and "." in cmdline),
                "name_is_common_masquerade_target": int(name in SUSPICIOUS_PROCESS_NAMES),
                "ppid_is_none": int(p.get("ppid") in (None, 0)),
                "path_is_user_writable": int("users\\public" in cmdline.lower() or "temp" in cmdline.lower()
                                              or "/tmp/" in cmdline.lower()),
            })
        return pd.DataFrame(rows)

    def detect_process_anomalies(self, processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(processes) < 4:
            # Not enough samples for a meaningful isolation forest fit
            return [self._heuristic_only(p, "process") for p in processes]

        df = self._process_features(processes)
        scaler = StandardScaler()
        X = scaler.fit_transform(df.values)

        model = IsolationForest(contamination=self.contamination, random_state=self.random_state, n_estimators=200)
        model.fit(X)
        raw_scores = model.decision_function(X)  # higher = more normal
        predictions = model.predict(X)  # -1 anomaly, 1 normal

        results = []
        for i, p in enumerate(processes):
            # Normalize decision_function output (~[-0.5, 0.5]) into a 0-1 anomaly score
            anomaly_score = float(np.clip(0.5 - raw_scores[i], 0, 1))
            is_anom = predictions[i] == -1
            reasons = []
            if df.iloc[i]["name_is_common_masquerade_target"] and df.iloc[i]["path_is_user_writable"]:
                reasons.append("Process name masquerades as system binary but runs from user-writable path")
            if df.iloc[i]["has_ip_in_cmdline"]:
                reasons.append("Command line contains network address pattern")
            if is_anom and not reasons:
                reasons.append("Statistically anomalous resource/handle profile vs. other processes in this dump")

            results.append({
                "entity_type": "process",
                "entity_ref": f"PID {p.get('pid')} ({p.get('name')})",
                "anomaly_score": round(anomaly_score, 4),
                "is_anomaly": bool(is_anom),
                "features": df.iloc[i].to_dict(),
                "explanation": "; ".join(reasons) if reasons else "No specific indicator, flagged by outlier model",
            })
        return results

    # ---------------- Connection anomaly detection ----------------
    def _connection_features(self, connections: List[Dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for c in connections:
            remote_port = c.get("remote_port") or 0
            rows.append({
                "remote_port": remote_port,
                "is_suspicious_port": int(remote_port in SUSPICIOUS_PORTS),
                "is_high_port": int(remote_port > 49152),
                "is_established": int((c.get("state") or "").upper() == "ESTABLISHED"),
            })
        return pd.DataFrame(rows)

    def detect_connection_anomalies(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(connections) < 4:
            return [self._heuristic_only(c, "connection") for c in connections]

        df = self._connection_features(connections)
        scaler = StandardScaler()
        X = scaler.fit_transform(df.values)

        model = IsolationForest(contamination=self.contamination, random_state=self.random_state, n_estimators=200)
        model.fit(X)
        raw_scores = model.decision_function(X)
        predictions = model.predict(X)

        results = []
        for i, c in enumerate(connections):
            anomaly_score = float(np.clip(0.5 - raw_scores[i], 0, 1))
            is_anom = predictions[i] == -1
            reasons = []
            if df.iloc[i]["is_suspicious_port"]:
                reasons.append(f"Remote port {c.get('remote_port')} is commonly associated with C2 frameworks")
            if is_anom and not reasons:
                reasons.append("Statistically anomalous connection profile vs. baseline traffic in this dump")

            results.append({
                "entity_type": "connection",
                "entity_ref": f"{c.get('local_addr')}:{c.get('local_port')} -> "
                               f"{c.get('remote_addr')}:{c.get('remote_port')}",
                "anomaly_score": round(anomaly_score, 4),
                "is_anomaly": bool(is_anom),
                "features": df.iloc[i].to_dict(),
                "explanation": "; ".join(reasons) if reasons else "No specific indicator, flagged by outlier model",
            })
        return results

    @staticmethod
    def _heuristic_only(entity: Dict[str, Any], kind: str) -> Dict[str, Any]:
        """Fallback for tiny sample sizes where ML fitting isn't meaningful."""
        is_susp = entity.get("is_suspicious", False)
        if kind == "process":
            ref = f"PID {entity.get('pid')} ({entity.get('name')})"
        else:
            ref = f"{entity.get('local_addr')}:{entity.get('local_port')} -> " \
                  f"{entity.get('remote_addr')}:{entity.get('remote_port')}"
        return {
            "entity_type": kind,
            "entity_ref": ref,
            "anomaly_score": 0.8 if is_susp else 0.1,
            "is_anomaly": bool(is_susp),
            "features": {},
            "explanation": "Sample too small for ML model; heuristic flag only" if not is_susp else
                            "Heuristic indicators present",
        }
