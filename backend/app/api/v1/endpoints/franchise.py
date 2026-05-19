"""Franchise management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.franchise.service import FranchiseService

router = APIRouter()


class MenuPushRequest(BaseModel):
    source_branch_id: str
    target_branch_ids: List[str]


@router.post("/menu/push")
async def push_menu(
    data: MenuPushRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Push menu from one branch to others."""
    if current_user.get("role") not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Admin or manager only")

    franchise_service = FranchiseService(db)
    return franchise_service.push_menu_to_branches(
        tenant_id=current_user["tenant_id"],
        source_branch_id=data.source_branch_id,
        target_branch_ids=data.target_branch_ids
    )


@router.get("/outlet-comparison")
async def outlet_comparison(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Compare performance across outlets."""
    franchise_service = FranchiseService(db)
    return franchise_service.get_outlet_comparison(
        tenant_id=current_user["tenant_id"],
        date_from=date_from,
        date_to=date_to
    )


@router.get("/centralized-inventory")
async def centralized_inventory(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get inventory across all branches."""
    franchise_service = FranchiseService(db)
    return franchise_service.get_centralized_inventory(current_user["tenant_id"])
