"""Profitability analytics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.report.profitability import ProfitabilityService

router = APIRouter()


@router.get("/items")
async def item_profitability(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ProfitabilityService(db)
    return service.get_item_profitability(
        current_user["tenant_id"], branch_id, date_from, date_to
    )


@router.get("/categories")
async def category_profitability(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ProfitabilityService(db)
    return service.get_category_profitability(current_user["tenant_id"], branch_id)


@router.get("/branches")
async def branch_profitability(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ProfitabilityService(db)
    return service.get_branch_profitability(current_user["tenant_id"])
