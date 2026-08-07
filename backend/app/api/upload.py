"""
Memory dump upload endpoint. Validates, saves, records the Analysis
row, and enqueues the Celery analysis task.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import Analysis, AnalysisStatus, get_db
from app.models.schemas import AnalysisOut
from app.utils.file_utils import detect_format, save_upload_file, validate_extension
from app.utils.security import get_current_token_payload
from app.workers.tasks import run_analysis

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
async def upload_dump(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_current_token_payload),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not validate_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    file_path, size, sha256_hex = await save_upload_file(file, settings.UPLOAD_DIR)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")

    from pathlib import Path
    dump_format = detect_format(file_path, Path(file.filename).suffix)

    analysis = Analysis(
        filename=file.filename,
        file_path=file_path,
        file_size=size,
        file_hash_sha256=sha256_hex,
        dump_format=dump_format,
        status=AnalysisStatus.QUEUED,
        owner_id=token.sub,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    run_analysis.delay(analysis.id)

    return analysis
