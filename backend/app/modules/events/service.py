"""Event sourcing service for order events."""

import uuid
import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, JSON, DateTime, Integer, Text
from app.infrastructure.database import Base
from app.models import generate_uuid


class EventStore(Base):
    __tablename__ = "event_store"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    aggregate_type = Column(String(50), nullable=False)  # order, payment, etc.
    aggregate_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    extra_metadata = Column("event_metadata", JSON, default={})
    version = Column(Integer, nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)


class EventSourcingService:
    def __init__(self, db: Session):
        self.db = db

    def append_event(self, aggregate_type: str, aggregate_id: str,
                     event_type: str, event_data: dict,
                     tenant_id: str, user_id: str = None,
                     metadata: dict = None) -> EventStore:
        """Append an event to the event store."""
        # Get current version
        last_event = self.db.query(EventStore).filter(
            EventStore.aggregate_type == aggregate_type,
            EventStore.aggregate_id == aggregate_id
        ).order_by(EventStore.version.desc()).first()

        version = (last_event.version + 1) if last_event else 1

        event = EventStore(
            id=str(uuid.uuid4()),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            event_data=event_data,
            metadata=metadata or {},
            version=version,
            tenant_id=tenant_id,
            user_id=user_id
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(self, aggregate_type: str, aggregate_id: str,
                   from_version: int = 0) -> List[EventStore]:
        """Get all events for an aggregate."""
        return self.db.query(EventStore).filter(
            EventStore.aggregate_type == aggregate_type,
            EventStore.aggregate_id == aggregate_id,
            EventStore.version > from_version
        ).order_by(EventStore.version.asc()).all()

    def get_events_by_type(self, tenant_id: str, event_type: str,
                           skip: int = 0, limit: int = 100) -> List[EventStore]:
        """Get events by type."""
        return self.db.query(EventStore).filter(
            EventStore.tenant_id == tenant_id,
            EventStore.event_type == event_type
        ).order_by(EventStore.created_at.desc()).offset(skip).limit(limit).all()

    def get_aggregate_events(self, tenant_id: str, aggregate_type: str,
                             skip: int = 0, limit: int = 100) -> List[EventStore]:
        """Get all events for an aggregate type."""
        return self.db.query(EventStore).filter(
            EventStore.tenant_id == tenant_id,
            EventStore.aggregate_type == aggregate_type
        ).order_by(EventStore.created_at.desc()).offset(skip).limit(limit).all()

    def replay_events(self, aggregate_type: str, aggregate_id: str) -> dict:
        """Replay events to reconstruct aggregate state."""
        events = self.get_events(aggregate_type, aggregate_id)

        state = {}
        for event in events:
            self._apply_event(state, event.event_type, event.event_data)

        return state

    def _apply_event(self, state: dict, event_type: str, event_data: dict):
        """Apply an event to reconstruct state."""
        if event_type == "order.created":
            state.update(event_data)
            state["items"] = event_data.get("items", [])
            state["status"] = "pending"

        elif event_type == "order.status_changed":
            state["status"] = event_data.get("new_status")
            state["previous_status"] = event_data.get("old_status")

        elif event_type == "order.item_added":
            if "items" not in state:
                state["items"] = []
            state["items"].append(event_data.get("item"))

        elif event_type == "order.payment_added":
            if "payments" not in state:
                state["payments"] = []
            state["payments"].append(event_data)

        elif event_type == "order.discount_applied":
            state["discount"] = event_data.get("discount")
            state["total"] = event_data.get("new_total")
