"""Webhook system for third-party integrations."""

import uuid
import hmac
import hashlib
import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer, Text
from app.infrastructure.database import Base
from app.models import generate_uuid


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    url = Column(Text, nullable=False)
    secret = Column(String(255), nullable=False)
    events = Column(JSON, default=[])  # ["order.created", "payment.completed", ...]
    is_active = Column(Boolean, default=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    webhook_id = Column(String(36), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    payload = Column(JSON)
    status = Column(String(20), default="pending")  # pending, success, failed
    response_code = Column(Integer)
    response_body = Column(Text)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)


class WebhookService:
    def __init__(self, db: Session):
        self.db = db

    def create_webhook(self, tenant_id: str, url: str, events: list, description: str = "") -> Webhook:
        secret = uuid.uuid4().hex
        webhook = Webhook(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            url=url,
            secret=secret,
            events=events,
            description=description
        )
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def get_webhooks(self, tenant_id: str) -> List[Webhook]:
        return self.db.query(Webhook).filter(
            Webhook.tenant_id == tenant_id,
            Webhook.is_active == True
        ).all()

    def delete_webhook(self, webhook_id: str, tenant_id: str) -> bool:
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id
        ).first()
        if webhook:
            webhook.is_active = False
            self.db.commit()
            return True
        return False

    def generate_signature(self, secret: str, payload: dict) -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode()
        return hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

    def dispatch_event(self, tenant_id: str, event: str, payload: dict):
        """Dispatch event to all matching webhooks."""
        webhooks = self.db.query(Webhook).filter(
            Webhook.tenant_id == tenant_id,
            Webhook.is_active == True
        ).all()

        for webhook in webhooks:
            if event in (webhook.events or []) or "*" in (webhook.events or []):
                delivery = WebhookDelivery(
                    id=str(uuid.uuid4()),
                    webhook_id=webhook.id,
                    event=event,
                    payload=payload,
                    status="pending",
                    created_at=datetime.utcnow()
                )
                self.db.add(delivery)

        self.db.commit()

    def get_deliveries(self, webhook_id: str, skip: int = 0, limit: int = 50) -> List[WebhookDelivery]:
        return self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id
        ).order_by(
            WebhookDelivery.created_at.desc()
        ).offset(skip).limit(limit).all()
