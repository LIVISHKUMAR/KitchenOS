"""Table reservation and waitlist endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid
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


# --- Waitlist ---

_waitlist: list = []


class WaitlistEntry(BaseModel):
    customer_name: str
    customer_phone: str
    party_size: int
    notes: Optional[str] = None


@router.post("/waitlist", status_code=201)
async def add_to_waitlist(
    data: WaitlistEntry,
    current_user: dict = Depends(get_current_user),
):
    """Add a walk-in customer to the waitlist."""
    entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user["tenant_id"],
        "branch_id": current_user.get("branch_id"),
        "customer_name": data.customer_name,
        "customer_phone": data.customer_phone,
        "party_size": data.party_size,
        "notes": data.notes,
        "status": "waiting",
        "estimated_wait_minutes": 30,
        "created_at": datetime.utcnow().isoformat(),
    }
    _waitlist.append(entry)
    return entry


@router.get("/waitlist")
async def get_waitlist(
    current_user: dict = Depends(get_current_user),
):
    """Get current waitlist for this tenant."""
    return [w for w in _waitlist if w["tenant_id"] == current_user["tenant_id"] and w["status"] == "waiting"]


@router.put("/waitlist/{entry_id}/seat")
async def seat_from_waitlist(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark waitlist entry as seated."""
    for w in _waitlist:
        if w["id"] == entry_id and w["tenant_id"] == current_user["tenant_id"]:
            w["status"] = "seated"
            return {"id": entry_id, "status": "seated"}
    raise HTTPException(status_code=404, detail="Entry not found")


@router.delete("/waitlist/{entry_id}")
async def remove_from_waitlist(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove entry from waitlist."""
    for w in _waitlist:
        if w["id"] == entry_id and w["tenant_id"] == current_user["tenant_id"]:
            w["status"] = "removed"
            return {"id": entry_id, "message": "Removed"}
    raise HTTPException(status_code=404, detail="Entry not found")
