"""
Celery background tasks. Runs the forensics pipeline and persists
results using a synchronous SQLAlchemy session (Celery workers run
outside the FastAPI async event loop). Publishes progress to Redis
pub/sub so the WebSocket layer in the API process can relay it to
connected clients in real time.
"""
import json
import logging
from datetime import datetime

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.database import (Analysis, AnalysisStatus, MLFinding,
                                  NetworkConnection, ProcessRecord, YaraMatch)
from app.services.analysis_service import AnalysisService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def _publish_progress(analysis_id: str, status: str, progress: int, stage: str, message: str):
    payload = {
        "analysis_id": analysis_id,
        "status": status,
        "progress": progress,
        "stage": stage,
        "message": message,
    }
    try:
        redis_client.publish(f"analysis:{analysis_id}", json.dumps(payload))
    except redis.RedisError as exc:
        logger.warning("Failed to publish progress to redis: %s", exc)


@celery_app.task(bind=True, name="app.workers.tasks.run_analysis")
def run_analysis(self, analysis_id: str):
    session = SyncSessionLocal()
    try:
        analysis = session.query(Analysis).filter(Analysis.id == analysis_id).one_or_none()
        if not analysis:
            logger.error("Analysis %s not found for task", analysis_id)
            return

        analysis.status = AnalysisStatus.RUNNING
        analysis.started_at = datetime.utcnow()
        analysis.celery_task_id = self.request.id
        session.commit()

        _publish_progress(analysis_id, AnalysisStatus.RUNNING.value, 0, "init", "Analysis started")

        def progress_cb(pct, stage, msg):
            analysis.progress = pct
            session.commit()
            _publish_progress(analysis_id, AnalysisStatus.RUNNING.value, pct, stage, msg)

        service = AnalysisService(analysis.file_path, analysis.dump_format)
        results = service.run(progress_cb=progress_cb)

        for p in results["processes"]:
            session.add(ProcessRecord(
                analysis_id=analysis_id,
                pid=p["pid"], ppid=p.get("ppid"), name=p["name"],
                threads=p.get("threads", 0), handles=p.get("handles", 0),
                cmdline=p.get("cmdline"),
                is_suspicious=p.get("is_suspicious", False),
                suspicion_reasons=p.get("suspicion_reasons", []),
            ))

        for c in results["connections"]:
            session.add(NetworkConnection(
                analysis_id=analysis_id,
                pid=c.get("pid"), process_name=c.get("process_name"),
                local_addr=c.get("local_addr"), local_port=c.get("local_port"),
                remote_addr=c.get("remote_addr"), remote_port=c.get("remote_port"),
                protocol=c.get("protocol"), state=c.get("state"),
                is_suspicious=c.get("is_suspicious", False),
            ))

        for m in results["yara_matches"]:
            session.add(YaraMatch(
                analysis_id=analysis_id,
                rule_name=m["rule_name"], rule_namespace=m.get("rule_namespace"),
                matched_pid=m.get("matched_pid"), offset=m.get("offset"),
                severity=m.get("severity", "medium"), tags=m.get("tags", []),
                strings_matched=m.get("strings_matched", []),
            ))

        for f in results["ml_findings"]:
            session.add(MLFinding(
                analysis_id=analysis_id,
                entity_type=f["entity_type"], entity_ref=f["entity_ref"],
                anomaly_score=f["anomaly_score"], is_anomaly=f["is_anomaly"],
                features=f.get("features", {}), explanation=f.get("explanation"),
            ))

        analysis.status = AnalysisStatus.COMPLETED
        analysis.progress = 100
        analysis.completed_at = datetime.utcnow()
        session.commit()

        _publish_progress(analysis_id, AnalysisStatus.COMPLETED.value, 100, "complete", "Analysis complete")

    except Exception as exc:
        logger.exception("Analysis %s failed", analysis_id)
        session.rollback()
        analysis = session.query(Analysis).filter(Analysis.id == analysis_id).one_or_none()
        if analysis:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(exc)
            session.commit()
        _publish_progress(analysis_id, AnalysisStatus.FAILED.value, 0, "error", str(exc))
        raise
    finally:
        session.close()
