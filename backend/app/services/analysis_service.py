"""
Core analysis orchestration: ties together Volatility, YARA, and ML
services, persists results, and reports progress.
"""
import logging
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (Analysis, AnalysisStatus, MLFinding,
                                  NetworkConnection, ProcessRecord, YaraMatch)
from app.services.ml_service import MLAnomalyService
from app.services.volatility_service import VolatilityService
from app.services.yara_service import YaraService

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[int, str, str], None]]


class AnalysisService:
    """
    Runs the full pipeline for a single Analysis row. Designed to be
    called from a Celery task (sync context) — the DB session passed
    in should be a sync session there, but this class only needs
    plain dict-like access, so it's kept ORM-session agnostic where
    possible and the Celery task handles persistence.
    """

    def __init__(self, dump_path: str, dump_format):
        self.volatility = VolatilityService(dump_path, dump_format)
        self.yara = YaraService()
        self.ml = MLAnomalyService()
        self.dump_path = dump_path

    def run(self, progress_cb: ProgressCallback = None) -> dict:
        def report(pct, stage, msg):
            logger.info("[%s] %s%% - %s", stage, pct, msg)
            if progress_cb:
                progress_cb(pct, stage, msg)

        report(5, "init", "Starting analysis pipeline")

        report(15, "volatility", "Extracting process list")
        processes = self.volatility.extract_processes()

        report(35, "volatility", "Extracting network connections")
        connections = self.volatility.extract_connections()

        report(50, "yara", "Scanning memory image against YARA ruleset")
        yara_matches = self.yara.scan_file(self.dump_path)

        report(70, "ml", "Running anomaly detection on processes")
        process_findings = self.ml.detect_process_anomalies(processes)

        report(85, "ml", "Running anomaly detection on network connections")
        connection_findings = self.ml.detect_connection_anomalies(connections)

        report(95, "finalize", "Compiling results")

        summary = {
            "total_processes": len(processes),
            "suspicious_processes": sum(1 for p in processes if p.get("is_suspicious")),
            "total_connections": len(connections),
            "suspicious_connections": sum(1 for c in connections if c.get("is_suspicious")),
            "yara_matches": len(yara_matches),
            "critical_yara_matches": sum(1 for m in yara_matches if m.get("severity") == "critical"),
            "ml_anomalies": sum(1 for f in process_findings + connection_findings if f.get("is_anomaly")),
        }

        report(100, "complete", "Analysis complete")

        return {
            "processes": processes,
            "connections": connections,
            "yara_matches": yara_matches,
            "ml_findings": process_findings + connection_findings,
            "summary": summary,
        }


async def get_analysis_or_404(db: AsyncSession, analysis_id: str) -> Analysis:
    from fastapi import HTTPException, status
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis
