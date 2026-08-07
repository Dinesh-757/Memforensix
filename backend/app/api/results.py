"""
Results endpoints: full analysis results, filtered process/connection
lists, and report export (PDF/JSON/CSV).
"""
import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Analysis, get_db
from app.models.schemas import AnalysisResultsOut
from app.services.analysis_service import get_analysis_or_404
from app.utils.security import get_current_token_payload

router = APIRouter(prefix="/results", tags=["results"])


async def _load_full_analysis(db: AsyncSession, analysis_id: str) -> Analysis:
    result = await db.execute(
        select(Analysis)
        .options(
            selectinload(Analysis.processes),
            selectinload(Analysis.connections),
            selectinload(Analysis.yara_matches),
            selectinload(Analysis.ml_findings),
        )
        .where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/{analysis_id}", response_model=AnalysisResultsOut)
async def get_results(analysis_id: str, db: AsyncSession = Depends(get_db),
                       token=Depends(get_current_token_payload)):
    analysis = await _load_full_analysis(db, analysis_id)

    summary = {
        "total_processes": len(analysis.processes),
        "suspicious_processes": sum(1 for p in analysis.processes if p.is_suspicious),
        "total_connections": len(analysis.connections),
        "suspicious_connections": sum(1 for c in analysis.connections if c.is_suspicious),
        "yara_matches": len(analysis.yara_matches),
        "critical_yara_matches": sum(1 for m in analysis.yara_matches if m.severity == "critical"),
        "ml_anomalies": sum(1 for f in analysis.ml_findings if f.is_anomaly),
    }

    return AnalysisResultsOut(
        analysis=analysis,
        processes=analysis.processes,
        connections=analysis.connections,
        yara_matches=analysis.yara_matches,
        ml_findings=analysis.ml_findings,
        summary=summary,
    )


@router.get("/{analysis_id}/export")
async def export_results(
    analysis_id: str,
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_current_token_payload),
):
    analysis = await _load_full_analysis(db, analysis_id)

    if format == "json":
        data = {
            "analysis_id": analysis.id,
            "filename": analysis.filename,
            "sha256": analysis.file_hash_sha256,
            "status": analysis.status.value,
            "generated_at": datetime.utcnow().isoformat(),
            "processes": [{"pid": p.pid, "name": p.name, "is_suspicious": p.is_suspicious,
                            "suspicion_reasons": p.suspicion_reasons} for p in analysis.processes],
            "connections": [{"remote": f"{c.remote_addr}:{c.remote_port}", "process": c.process_name,
                              "is_suspicious": c.is_suspicious} for c in analysis.connections],
            "yara_matches": [{"rule": m.rule_name, "severity": m.severity, "tags": m.tags}
                              for m in analysis.yara_matches],
            "ml_findings": [{"entity": f.entity_ref, "score": f.anomaly_score, "is_anomaly": f.is_anomaly}
                             for f in analysis.ml_findings],
        }
        buf = io.BytesIO(json.dumps(data, indent=2).encode("utf-8"))
        return StreamingResponse(buf, media_type="application/json", headers={
            "Content-Disposition": f'attachment; filename="{analysis.id}_report.json"'
        })

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Type", "Identifier", "Detail", "Suspicious/Severity"])
        for p in analysis.processes:
            writer.writerow(["Process", f"PID {p.pid}", p.name, "SUSPICIOUS" if p.is_suspicious else "normal"])
        for c in analysis.connections:
            writer.writerow(["Connection", f"{c.local_addr}:{c.local_port}",
                              f"-> {c.remote_addr}:{c.remote_port}", "SUSPICIOUS" if c.is_suspicious else "normal"])
        for m in analysis.yara_matches:
            writer.writerow(["YARA Match", m.rule_name, ",".join(m.tags or []), m.severity])
        for f in analysis.ml_findings:
            writer.writerow(["ML Finding", f.entity_ref, f.explanation, f.anomaly_score])
        mem = io.BytesIO(buf.getvalue().encode("utf-8"))
        return StreamingResponse(mem, media_type="text/csv", headers={
            "Content-Disposition": f'attachment; filename="{analysis.id}_report.csv"'
        })

    # PDF
    from app.services.report_service import generate_pdf_report
    pdf_bytes = generate_pdf_report(analysis)
    buf = io.BytesIO(pdf_bytes)
    return StreamingResponse(buf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{analysis.id}_report.pdf"'
    })
