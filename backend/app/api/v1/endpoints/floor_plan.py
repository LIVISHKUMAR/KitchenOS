"""Floor plan endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.table.floor_plan import FloorPlanService

router = APIRouter()


class FloorPlanCreate(BaseModel):
    name: str
    tables: list  # [{id, number, x, y, width, height, shape}]


class TablePosition(BaseModel):
    table_id: str
    x: int
    y: int


@router.get("/{branch_id}")
async def get_floor_plan(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get floor plan with live table status."""
    service = FloorPlanService(db)
    return service.get_floor_plan(branch_id)


@router.post("/", status_code=201)
async def create_floor_plan(
    data: FloorPlanCreate,
    branch_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create a floor plan."""
    service = FloorPlanService(db)
    return service.create_floor_plan(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id or current_user.get("branch_id", ""),
        name=data.name,
        tables=data.tables
    )


@router.put("/{plan_id}/table-position")
async def update_table_position(
    plan_id: str,
    data: TablePosition,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update a table's position (drag-drop)."""
    service = FloorPlanService(db)
    if not service.update_table_position(plan_id, data.table_id, data.x, data.y):
        raise HTTPException(status_code=404, detail="Floor plan not found")
    return {"message": "Position updated"}


@router.get("/{branch_id}/sections")
async def get_sections(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get unique sections for a branch."""
    service = FloorPlanService(db)
    return service.get_sections(branch_id)
