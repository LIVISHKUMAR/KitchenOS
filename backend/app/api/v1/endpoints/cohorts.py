"""Cohort analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.analytics.cohort import CohortAnalysisService

router = APIRouter()


@router.get("/retention")
async def retention_cohorts(
    months_back: int = Query(default=6, le=12),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = CohortAnalysisService(db)
    return service.get_retention_cohorts(current_user["tenant_id"], months_back)


@router.get("/revenue")
async def revenue_cohorts(
    months_back: int = Query(default=6, le=12),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = CohortAnalysisService(db)
    return service.get_revenue_cohorts(current_user["tenant_id"], months_back)


@router.get("/behavior")
async def behavior_cohorts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = CohortAnalysisService(db)
    return service.get_behavior_cohorts(current_user["tenant_id"])
