"""Menu scheduling endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, time
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.menu.scheduling import MenuSchedulingService

router = APIRouter()


class ScheduleCreate(BaseModel):
    name: str
    schedule_type: str  # time_based, seasonal, special
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None
    days_of_week: Optional[list] = [0, 1, 2, 3, 4, 5, 6]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    menu_items: list = []
    branch_id: Optional[str] = None


@router.post("/", status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = MenuSchedulingService(db)
    schedule_data = data.model_dump()
    if schedule_data.get("start_time"):
        schedule_data["start_time"] = datetime.strptime(schedule_data["start_time"], "%H:%M").time()
    if schedule_data.get("end_time"):
        schedule_data["end_time"] = datetime.strptime(schedule_data["end_time"], "%H:%M").time()
    return service.create_schedule(current_user["tenant_id"], schedule_data)


@router.get("/")
async def list_schedules(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = MenuSchedulingService(db)
    return service.get_schedules(current_user["tenant_id"], branch_id)


@router.get("/active-menu")
async def get_active_menu(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get currently available menu based on schedules."""
    service = MenuSchedulingService(db)
    return service.get_active_menu(current_user["tenant_id"], branch_id)


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = MenuSchedulingService(db)
    if not service.delete_schedule(schedule_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted"}
