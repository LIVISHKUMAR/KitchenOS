from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.report.service import ReportService

router = APIRouter()


@router.get("/daily-sales")
async def daily_sales_report(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.daily_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date=date
    )


@router.get("/item-wise-sales")
async def item_wise_sales_report(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.item_wise_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/category-wise-sales")
async def category_wise_sales_report(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.category_wise_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/hourly-sales")
async def hourly_sales_report(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    report_service = ReportService(db)
    return report_service.hourly_sales(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date=date
    )
