"""
Analysis listing, status, and deletion endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Analysis, get_db
from app.models.schemas import AnalysisListOut, AnalysisOut
from app.services.analysis_service import get_analysis_or_404
from app.utils.security import get_current_token_payload, require_role

router = APIRouter(prefix="/analyses", tags=["analysis"])


@router.get("", response_model=AnalysisListOut)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_current_token_payload),
):
    count_result = await db.execute(select(func.count()).select_from(Analysis).where(Analysis.owner_id == token.sub))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Analysis)
        .where(Analysis.owner_id == token.sub)
        .order_by(Analysis.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return AnalysisListOut(total=total, items=items)


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db),
                        token=Depends(get_current_token_payload)):
    return await get_analysis_or_404(db, analysis_id)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    token=Depends(require_role("admin", "analyst")),
):
    analysis = await get_analysis_or_404(db, analysis_id)
    await db.delete(analysis)
    await db.commit()
