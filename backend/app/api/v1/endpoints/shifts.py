from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, time
import uuid
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.models import Shift, ShiftAssignment

router = APIRouter()


class ShiftCreate(BaseModel):
    name: str
    branch_id: str
    start_time: str  # HH:MM format
    end_time: str
    break_duration_minutes: int = 30
    is_night_shift: bool = False


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_duration_minutes: Optional[int] = None
    is_night_shift: Optional[bool] = None
    is_active: Optional[bool] = None


class ShiftResponse(BaseModel):
    id: str
    branch_id: str
    name: str
    start_time: str
    end_time: str
    break_duration_minutes: int
    is_night_shift: bool
    is_active: bool

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    shift_id: str
    user_id: str
    date: str  # YYYY-MM-DD


@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift: ShiftCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    db_shift = Shift(
        id=str(uuid.uuid4()),
        branch_id=shift.branch_id,
        name=shift.name,
        start_time=datetime.strptime(shift.start_time, "%H:%M").time(),
        end_time=datetime.strptime(shift.end_time, "%H:%M").time(),
        break_duration_minutes=shift.break_duration_minutes,
        is_night_shift=shift.is_night_shift,
        is_active=True
    )
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return {
        "id": str(db_shift.id),
        "branch_id": str(db_shift.branch_id),
        "name": db_shift.name,
        "start_time": db_shift.start_time.strftime("%H:%M"),
        "end_time": db_shift.end_time.strftime("%H:%M"),
        "break_duration_minutes": db_shift.break_duration_minutes,
        "is_night_shift": db_shift.is_night_shift,
        "is_active": db_shift.is_active
    }


@router.get("/", response_model=List[ShiftResponse])
async def list_shifts(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    shifts = db.query(Shift).filter(Shift.branch_id == branch_id).all()
    return [
        {
            "id": str(s.id),
            "branch_id": str(s.branch_id),
            "name": s.name,
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
            "break_duration_minutes": s.break_duration_minutes,
            "is_night_shift": s.is_night_shift,
            "is_active": s.is_active
        }
        for s in shifts
    ]


@router.post("/assign")
async def assign_shift(
    data: AssignmentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    assignment = ShiftAssignment(
        id=str(uuid.uuid4()),
        shift_id=data.shift_id,
        user_id=data.user_id,
        date=datetime.strptime(data.date, "%Y-%m-%d").date(),
        status="scheduled"
    )
    db.add(assignment)
    db.commit()
    return {"id": str(assignment.id), "status": "scheduled", "message": "Shift assigned"}


@router.post("/checkin/{assignment_id}")
async def check_in(
    assignment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    assignment = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.check_in = datetime.utcnow()
    assignment.status = "checked_in"
    db.commit()
    return {"id": str(assignment.id), "check_in": assignment.check_in.isoformat(), "status": "checked_in"}


@router.post("/checkout/{assignment_id}")
async def check_out(
    assignment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    assignment = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.check_out = datetime.utcnow()
    assignment.status = "checked_out"
    if assignment.check_in:
        delta = assignment.check_out - assignment.check_in
        assignment.work_hours = round(delta.total_seconds() / 3600, 2)
    db.commit()
    return {
        "id": str(assignment.id),
        "check_out": assignment.check_out.isoformat(),
        "work_hours": assignment.work_hours,
        "status": "checked_out"
    }


@router.get("/assignments")
async def list_assignments(
    branch_id: str,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    query = db.query(ShiftAssignment).join(Shift).filter(Shift.branch_id == branch_id)
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        query = query.filter(ShiftAssignment.date == target_date)
    assignments = query.all()
    return [
        {
            "id": str(a.id),
            "shift_id": str(a.shift_id),
            "user_id": str(a.user_id),
            "date": a.date.isoformat() if a.date else None,
            "status": a.status,
            "check_in": a.check_in.isoformat() if a.check_in else None,
            "check_out": a.check_out.isoformat() if a.check_out else None,
            "work_hours": a.work_hours
        }
        for a in assignments
    ]
