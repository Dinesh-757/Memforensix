"""
YARA-based malware pattern scanning service.

Compiles all .yar/.yara rule files under settings.YARA_RULES_DIR and
scans the raw memory dump file against them. This is a real, working
scan — not a stub — but the bundled rules are intentionally broad
detection heuristics (packers, common C2 strings, process-hollowing
indicators) suitable for a demo/portfolio project rather than a
production threat-intel feed.
"""
import logging
import os
from typing import Any, Dict, List

import yara

from app.core.config import settings

logger = logging.getLogger(__name__)


class YaraService:
    def __init__(self, rules_dir: str = None):
        self.rules_dir = rules_dir or settings.YARA_RULES_DIR
        self._compiled = None

    def _compile_rules(self):
        if self._compiled is not None:
            return self._compiled

        if not os.path.isdir(self.rules_dir):
            logger.warning("YARA rules directory not found: %s", self.rules_dir)
            self._compiled = None
            return None

        filepaths = {}
        for fname in os.listdir(self.rules_dir):
            if fname.endswith((".yar", ".yara")):
                namespace = os.path.splitext(fname)[0]
                filepaths[namespace] = os.path.join(self.rules_dir, fname)

        if not filepaths:
            logger.warning("No YARA rule files found in %s", self.rules_dir)
            self._compiled = None
            return None

        try:
            self._compiled = yara.compile(filepaths=filepaths)
        except yara.Error as exc:
            logger.error("Failed to compile YARA rules: %s", exc)
            self._compiled = None
        return self._compiled

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a file on disk against compiled rules, return match dicts."""
        rules = self._compile_rules()
        if rules is None:
            return []

        matches = []
        try:
            yara_matches = rules.match(file_path, timeout=300)
        except yara.Error as exc:
            logger.error("YARA scan failed on %s: %s", file_path, exc)
            return []

        for m in yara_matches:
            matched_strings = []
            for s in m.strings[:10]:
                try:
                    matched_strings.append(s.identifier)
                except Exception:
                    pass
            matches.append({
                "rule_name": m.rule,
                "rule_namespace": m.namespace,
                "matched_pid": None,
                "offset": None,
                "severity": m.meta.get("severity", "medium"),
                "tags": list(m.tags),
                "strings_matched": matched_strings,
            })
        return matches
