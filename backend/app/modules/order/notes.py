"""Order notes and history tracking."""

import uuid
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, DateTime
from app.infrastructure.database import Base
from app.models import generate_uuid


class OrderNote(Base):
    __tablename__ = "order_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False)
    user_id = Column(String(36))
    note_type = Column(String(20), default="general")  # general, internal, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderHistory(Base):
    __tablename__ = "order_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False)
    user_id = Column(String(36))
    action = Column(String(50), nullable=False)  # status_change, item_added, discount_applied, etc.
    old_value = Column(Text)
    new_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderNotesService:
    def __init__(self, db: Session):
        self.db = db

    def add_note(self, order_id: str, tenant_id: str, user_id: str,
                 content: str, note_type: str = "general") -> OrderNote:
        note = OrderNote(
            id=str(uuid.uuid4()),
            order_id=order_id,
            tenant_id=tenant_id,
            user_id=user_id,
            note_type=note_type,
            content=content
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_notes(self, order_id: str) -> List[OrderNote]:
        return self.db.query(OrderNote).filter(
            OrderNote.order_id == order_id
        ).order_by(OrderNote.created_at.desc()).all()

    def add_history(self, order_id: str, tenant_id: str, user_id: str,
                    action: str, old_value: str = None, new_value: str = None) -> OrderHistory:
        entry = OrderHistory(
            id=str(uuid.uuid4()),
            order_id=order_id,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def get_history(self, order_id: str) -> List[OrderHistory]:
        return self.db.query(OrderHistory).filter(
            OrderHistory.order_id == order_id
        ).order_by(OrderHistory.created_at.desc()).all()
