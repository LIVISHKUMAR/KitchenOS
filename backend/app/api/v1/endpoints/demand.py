"""Demand forecasting endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.report.demand import DemandForecastService

router = APIRouter()


@router.get("/hourly-pattern")
async def hourly_pattern(
    branch_id: Optional[str] = None,
    days_back: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = DemandForecastService(db)
    return service.get_hourly_pattern(current_user["tenant_id"], branch_id, days_back)


@router.get("/daily-pattern")
async def daily_pattern(
    branch_id: Optional[str] = None,
    weeks_back: int = 4,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = DemandForecastService(db)
    return service.get_daily_pattern(current_user["tenant_id"], branch_id, weeks_back)


@router.get("/peak-hours")
async def peak_hours(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = DemandForecastService(db)
    return service.get_peak_hours(current_user["tenant_id"], branch_id)


@router.get("/forecast")
async def forecast_demand(
    target_date: str,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = DemandForecastService(db)
    return service.forecast_demand(current_user["tenant_id"], target_date, branch_id)
