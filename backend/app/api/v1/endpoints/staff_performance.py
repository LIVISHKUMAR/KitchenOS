"""Staff performance endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.report.staff import StaffPerformanceService

router = APIRouter()


@router.get("/")
async def staff_performance(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = StaffPerformanceService(db)
    return service.get_performance(current_user["tenant_id"], branch_id, date_from, date_to)


@router.get("/leaderboard")
async def staff_leaderboard(
    metric: str = "revenue",
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = StaffPerformanceService(db)
    return service.get_leaderboard(current_user["tenant_id"], metric, limit)
