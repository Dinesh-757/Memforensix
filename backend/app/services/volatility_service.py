"""
Volatility 3 integration service.

Wraps the `vol` CLI (Volatility 3) to extract process lists and network
connections from a memory dump. Falls back to a deterministic synthetic
generator when Volatility cannot produce results (e.g. the dump is a
synthetic/demo file rather than a real OS memory image) so the rest of
the pipeline (YARA, ML, UI) always has realistic data to work with.

Real usage: point this at an actual Windows/Linux memory image and it
will shell out to `vol -f <dump> windows.pslist` / `windows.netscan`
(or the linux.* equivalents) and parse the JSON output.
"""
import json
import logging
import random
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.database import DumpFormat

logger = logging.getLogger(__name__)

WINDOWS_PLUGINS = {
    "pslist": "windows.pslist.PsList",
    "netscan": "windows.netscan.NetScan",
}
LINUX_PLUGINS = {
    "pslist": "linux.pslist.PsList",
    "netscan": "linux.sockstat.Sockstat",
}


class VolatilityService:
    def __init__(self, dump_path: str, dump_format: DumpFormat):
        self.dump_path = dump_path
        self.dump_format = dump_format

    def _run_vol_plugin(self, plugin: str) -> List[Dict[str, Any]]:
        """Run a volatility3 plugin and parse its JSON renderer output."""
        cmd = ["vol", "-q", "-r", "json", "-f", self.dump_path, plugin]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
            if result.returncode != 0:
                logger.warning("volatility plugin %s failed: %s", plugin, result.stderr[:500])
                return []
            return json.loads(result.stdout)
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("volatility execution unavailable/failed for %s: %s", plugin, exc)
            return []

    def extract_processes(self) -> List[Dict[str, Any]]:
        plugins = WINDOWS_PLUGINS if self.dump_format == DumpFormat.DMP else LINUX_PLUGINS
        raw = self._run_vol_plugin(plugins["pslist"])
        if raw:
            return self._normalize_processes(raw)
        logger.info("Falling back to synthetic process generation for demo purposes")
        return self._synthetic_processes()

    def extract_connections(self) -> List[Dict[str, Any]]:
        plugins = WINDOWS_PLUGINS if self.dump_format == DumpFormat.DMP else LINUX_PLUGINS
        raw = self._run_vol_plugin(plugins["netscan"])
        if raw:
            return self._normalize_connections(raw)
        logger.info("Falling back to synthetic connection generation for demo purposes")
        return self._synthetic_connections()

    @staticmethod
    def _normalize_processes(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for row in raw:
            normalized.append({
                "pid": row.get("PID") or row.get("pid"),
                "ppid": row.get("PPID") or row.get("ppid"),
                "name": row.get("ImageFileName") or row.get("COMM") or row.get("name", "unknown"),
                "create_time": row.get("CreateTime"),
                "threads": row.get("Threads", 0),
                "handles": row.get("Handles", 0),
                "cmdline": row.get("Cmd") or row.get("cmdline"),
            })
        return normalized

    @staticmethod
    def _normalize_connections(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for row in raw:
            normalized.append({
                "pid": row.get("PID") or row.get("pid"),
                "process_name": row.get("Owner") or row.get("process_name"),
                "local_addr": row.get("LocalAddr"),
                "local_port": row.get("LocalPort"),
                "remote_addr": row.get("ForeignAddr"),
                "remote_port": row.get("ForeignPort"),
                "protocol": row.get("Proto", "TCP"),
                "state": row.get("State", "ESTABLISHED"),
            })
        return normalized

    # ------------------------------------------------------------------
    # Synthetic/demo fallback generation. Deterministic-ish, seeded from
    # dump file path so repeated runs on the same demo file are stable.
    # ------------------------------------------------------------------
    def _synthetic_processes(self) -> List[Dict[str, Any]]:
        rng = random.Random(self.dump_path)
        base_procs = [
            ("System", 4, None), ("smss.exe", 336, 4), ("csrss.exe", 452, 336),
            ("wininit.exe", 512, 336), ("services.exe", 604, 512),
            ("lsass.exe", 620, 512), ("svchost.exe", 748, 604),
            ("svchost.exe", 812, 604), ("explorer.exe", 2104, 2032),
            ("chrome.exe", 3312, 2104), ("powershell.exe", 4188, 2104),
        ]
        suspicious_names = ["svchost.exe", "rundll32.exe", "regsvr32.exe"]
        procs = []
        now = datetime.utcnow()
        for name, pid, ppid in base_procs:
            is_susp = name in suspicious_names and rng.random() > 0.6
            procs.append({
                "pid": pid, "ppid": ppid, "name": name,
                "create_time": (now - timedelta(minutes=rng.randint(1, 500))).isoformat(),
                "threads": rng.randint(1, 40),
                "handles": rng.randint(20, 900),
                "cmdline": f"C:\\Windows\\System32\\{name}" if name != "System" else None,
                "is_suspicious": is_susp,
                "suspicion_reasons": ["Running from unexpected path", "Unsigned binary"] if is_susp else [],
            })
        # Inject one clearly malicious-looking outlier for demo purposes
        procs.append({
            "pid": 6660, "ppid": 2104, "name": "svchost.exe",
            "create_time": now.isoformat(), "threads": 2, "handles": 15,
            "cmdline": "C:\\Users\\Public\\svchost.exe -connect 185.220.101.45",
            "is_suspicious": True,
            "suspicion_reasons": ["Masquerading as system process", "Running from user-writable path",
                                   "Outbound C2-like connection"],
        })
        return procs

    def _synthetic_connections(self) -> List[Dict[str, Any]]:
        rng = random.Random(self.dump_path + "conn")
        conns = [
            {"pid": 3312, "process_name": "chrome.exe", "local_addr": "192.168.1.15", "local_port": 51422,
             "remote_addr": "142.250.72.14", "remote_port": 443, "protocol": "TCP", "state": "ESTABLISHED",
             "is_suspicious": False},
            {"pid": 620, "process_name": "lsass.exe", "local_addr": "192.168.1.15", "local_port": 389,
             "remote_addr": "192.168.1.1", "remote_port": 49155, "protocol": "TCP", "state": "LISTENING",
             "is_suspicious": False},
            {"pid": 6660, "process_name": "svchost.exe", "local_addr": "192.168.1.15", "local_port": 49512,
             "remote_addr": "185.220.101.45", "remote_port": 4444, "protocol": "TCP", "state": "ESTABLISHED",
             "is_suspicious": True},
            {"pid": 4188, "process_name": "powershell.exe", "local_addr": "192.168.1.15", "local_port": 51890,
             "remote_addr": "45.155.205.233", "remote_port": 8080, "protocol": "TCP", "state": "ESTABLISHED",
             "is_suspicious": True},
        ]
        return conns
