"""Dynamic menu scheduling service."""

from typing import List, Optional, Dict
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Time
import uuid

from app.infrastructure.database import Base
from app.models import generate_uuid, MenuItem


class MenuSchedule(Base):
    __tablename__ = "menu_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), index=True)
    name = Column(String(100), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # time_based, seasonal, special
    start_time = Column(Time)
    end_time = Column(Time)
    days_of_week = Column(JSON, default=[0, 1, 2, 3, 4, 5, 6])  # 0=Mon, 6=Sun
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    menu_items = Column(JSON, default=[])  # List of menu_item_ids
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MenuSchedulingService:
    def __init__(self, db: Session):
        self.db = db

    def create_schedule(self, tenant_id: str, data: Dict) -> MenuSchedule:
        schedule = MenuSchedule(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            **data
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def get_active_menu(self, tenant_id: str, branch_id: str = None) -> List[Dict]:
        """Get currently available menu items based on schedules."""
        now = datetime.utcnow()
        current_time = now.time()
        current_day = now.weekday()

        # Get all active schedules
        query = self.db.query(MenuSchedule).filter(
            MenuSchedule.tenant_id == tenant_id,
            MenuSchedule.is_active == True
        )

        schedules = query.all()

        # Determine which items are available
        available_item_ids = set()

        for schedule in schedules:
            # Check time-based schedule
            if schedule.schedule_type == "time_based":
                if schedule.start_time and schedule.end_time:
                    if not (schedule.start_time <= current_time <= schedule.end_time):
                        continue
                if schedule.days_of_week and current_day not in schedule.days_of_week:
                    continue
                available_item_ids.update(schedule.menu_items)

            # Check seasonal schedule
            elif schedule.schedule_type == "seasonal":
                if schedule.start_date and schedule.end_date:
                    if not (schedule.start_date <= now <= schedule.end_date):
                        continue
                available_item_ids.update(schedule.menu_items)

            # Check special schedule
            elif schedule.schedule_type == "special":
                if schedule.start_date and schedule.end_date:
                    if not (schedule.start_date <= now <= schedule.end_date):
                        continue
                available_item_ids.update(schedule.menu_items)

        # If no schedules, return all available items
        if not available_item_ids:
            items = self.db.query(MenuItem).filter(
                MenuItem.tenant_id == tenant_id,
                MenuItem.is_available == True
            ).all()
        else:
            items = self.db.query(MenuItem).filter(
                MenuItem.id.in_(list(available_item_ids)),
                MenuItem.is_available == True
            ).all()

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "price": float(item.base_price),
                "is_veg": item.is_veg,
                "category_id": str(item.category_id) if item.category_id else None
            }
            for item in items
        ]

    def get_schedules(self, tenant_id: str, branch_id: str = None) -> List[MenuSchedule]:
        query = self.db.query(MenuSchedule).filter(
            MenuSchedule.tenant_id == tenant_id
        )
        if branch_id:
            query = query.filter(
                (MenuSchedule.branch_id == branch_id) | (MenuSchedule.branch_id == None)
            )
        return query.all()

    def delete_schedule(self, schedule_id: str, tenant_id: str) -> bool:
        schedule = self.db.query(MenuSchedule).filter(
            MenuSchedule.id == schedule_id,
            MenuSchedule.tenant_id == tenant_id
        ).first()
        if schedule:
            schedule.is_active = False
            self.db.commit()
            return True
        return False
