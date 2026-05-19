"""Shift management endpoints with cash reconciliation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.shift.service import ShiftService

router = APIRouter()


class StartShiftRequest(BaseModel):
    branch_id: str
    opening_cash: float = 0


class EndShiftRequest(BaseModel):
    closing_cash: float


@router.post("/start")
async def start_shift(
    data: StartShiftRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Start a new shift with opening cash."""
    service = ShiftService(db)
    result = service.start_shift(
        user_id=current_user["user_id"],
        branch_id=data.branch_id,
        opening_cash=data.opening_cash
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/end/{assignment_id}")
async def end_shift(
    assignment_id: str,
    data: EndShiftRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """End shift with cash reconciliation."""
    service = ShiftService(db)
    result = service.end_shift(
        assignment_id=assignment_id,
        closing_cash=data.closing_cash,
        user_id=current_user["user_id"]
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/active")
async def get_active_shift(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get current active shift."""
    service = ShiftService(db)
    result = service.get_active_shift(current_user["user_id"])
    if not result:
        return {"active": False}
    return {"active": True, **result}


@router.get("/report")
async def shift_report(
    branch_id: str,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get shift report for a branch."""
    service = ShiftService(db)
    return service.get_shift_report(branch_id, date)
