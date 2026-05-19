"""Table reservation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.reservation.service import ReservationService

router = APIRouter()


class ReservationCreate(BaseModel):
    branch_id: str
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    party_size: int = 2
    reservation_time: datetime
    duration_minutes: int = 60
    table_id: Optional[str] = None
    notes: Optional[str] = None


@router.post("/", status_code=201)
async def create_reservation(
    data: ReservationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ReservationService(db)
    return service.create_reservation(
        tenant_id=current_user["tenant_id"],
        branch_id=data.branch_id,
        data=data.model_dump()
    )


@router.get("/")
async def list_reservations(
    branch_id: str,
    date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ReservationService(db)
    return service.get_reservations(current_user["tenant_id"], branch_id, date, status)


@router.put("/{reservation_id}/status")
async def update_reservation_status(
    reservation_id: str,
    new_status: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ReservationService(db)
    result = service.update_status(reservation_id, new_status)
    if not result:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return result


@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ReservationService(db)
    if not service.cancel_reservation(reservation_id):
        raise HTTPException(status_code=400, detail="Cannot cancel reservation")
    return {"message": "Reservation cancelled"}


@router.get("/available-slots")
async def available_slots(
    branch_id: str,
    date: str,
    party_size: int = 2,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = ReservationService(db)
    return service.get_available_slots(branch_id, date, party_size)
