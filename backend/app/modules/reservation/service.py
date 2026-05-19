"""Table reservation system."""

import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from app.infrastructure.database import Base
from app.models import generate_uuid, DiningTable


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=False, index=True)
    table_id = Column(String(36), index=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20))
    customer_email = Column(String(255))
    party_size = Column(Integer, default=2)
    reservation_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(20), default="confirmed")  # confirmed, seated, completed, no_show, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReservationService:
    def __init__(self, db: Session):
        self.db = db

    def create_reservation(self, tenant_id: str, branch_id: str, data: dict) -> Reservation:
        # Find suitable table
        table_id = data.get("table_id")
        if not table_id:
            table_id = self._find_available_table(
                branch_id, data["party_size"],
                data["reservation_time"], data.get("duration_minutes", 60)
            )

        reservation = Reservation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            table_id=table_id,
            customer_name=data["customer_name"],
            customer_phone=data.get("customer_phone"),
            customer_email=data.get("customer_email"),
            party_size=data.get("party_size", 2),
            reservation_time=data["reservation_time"],
            duration_minutes=data.get("duration_minutes", 60),
            notes=data.get("notes")
        )
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def _find_available_table(self, branch_id: str, party_size: int,
                               reservation_time: datetime, duration: int) -> Optional[str]:
        """Find an available table for the reservation."""
        tables = self.db.query(DiningTable).filter(
            DiningTable.branch_id == branch_id,
            DiningTable.is_active == True,
            DiningTable.capacity >= party_size
        ).order_by(DiningTable.capacity.asc()).all()

        end_time = reservation_time + timedelta(minutes=duration)

        for table in tables:
            # Check for conflicting reservations
            conflict = self.db.query(Reservation).filter(
                Reservation.table_id == table.id,
                Reservation.status.in_(["confirmed", "seated"]),
                Reservation.reservation_time < end_time,
                Reservation.reservation_time + timedelta(minutes=Reservation.duration_minutes) > reservation_time
            ).first()

            if not conflict:
                return str(table.id)

        return None

    def get_reservations(self, tenant_id: str, branch_id: str,
                         date: Optional[str] = None, status: Optional[str] = None) -> List[Reservation]:
        query = self.db.query(Reservation).filter(
            Reservation.tenant_id == tenant_id,
            Reservation.branch_id == branch_id
        )
        if date:
            target = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(
                Reservation.reservation_time >= datetime.combine(target, datetime.min.time()),
                Reservation.reservation_time < datetime.combine(target + timedelta(days=1), datetime.min.time())
            )
        if status:
            query = query.filter(Reservation.status == status)
        return query.order_by(Reservation.reservation_time.asc()).all()

    def update_status(self, reservation_id: str, new_status: str) -> Optional[Reservation]:
        reservation = self.db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if reservation:
            reservation.status = new_status
            self.db.commit()
            self.db.refresh(reservation)
        return reservation

    def cancel_reservation(self, reservation_id: str) -> bool:
        reservation = self.db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if reservation and reservation.status == "confirmed":
            reservation.status = "cancelled"
            self.db.commit()
            return True
        return False

    def get_available_slots(self, branch_id: str, date: str, party_size: int) -> list:
        """Get available time slots for a given date."""
        target = datetime.strptime(date, "%Y-%m-%d").date()
        slots = []

        # Generate slots from 11:00 to 22:00 every 30 minutes
        for hour in range(11, 23):
            for minute in [0, 30]:
                slot_time = datetime.combine(target, datetime.min.time().replace(hour=hour, minute=minute))
                table_id = self._find_available_table(branch_id, party_size, slot_time, 60)
                if table_id:
                    slots.append({
                        "time": slot_time.strftime("%H:%M"),
                        "available": True
                    })

        return slots
