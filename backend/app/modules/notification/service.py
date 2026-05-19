"""Notification service for email, SMS, and push notifications."""

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Text
from app.infrastructure.database import Base
from app.models import generate_uuid


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    channel = Column(String(20), nullable=False)  # email, sms, push
    event = Column(String(100), nullable=False)  # order.ready, payment.success, etc.
    subject = Column(String(255))
    body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255))
    body = Column(Text)
    status = Column(String(20), default="pending")  # pending, sent, failed
    error = Column(Text)
    extra_data = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def send_email(self, to: str, subject: str, body: str, tenant_id: str) -> dict:
        """Send email notification.

        In production, integrate with SendGrid, SES, or SMTP.
        """
        log = NotificationLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel="email",
            recipient=to,
            subject=subject,
            body=body,
            status="sent",
            sent_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

        return {"id": str(log.id), "status": "sent", "channel": "email", "recipient": to}

    def send_sms(self, to: str, message: str, tenant_id: str) -> dict:
        """Send SMS notification.

        In production, integrate with Twilio, MSG91, or similar.
        """
        log = NotificationLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel="sms",
            recipient=to,
            body=message,
            status="sent",
            sent_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

        return {"id": str(log.id), "status": "sent", "channel": "sms", "recipient": to}

    def send_push(self, user_id: str, title: str, body: str, tenant_id: str) -> dict:
        """Send push notification.

        In production, integrate with Firebase Cloud Messaging.
        """
        log = NotificationLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel="push",
            recipient=user_id,
            subject=title,
            body=body,
            status="sent",
            sent_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

        return {"id": str(log.id), "status": "sent", "channel": "push", "recipient": user_id}

    def create_template(self, tenant_id: str, name: str, channel: str,
                        event: str, subject: str, body: str) -> NotificationTemplate:
        template = NotificationTemplate(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            channel=channel,
            event=event,
            subject=subject,
            body=body
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_templates(self, tenant_id: str, channel: Optional[str] = None) -> List[NotificationTemplate]:
        query = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.tenant_id == tenant_id,
            NotificationTemplate.is_active == True
        )
        if channel:
            query = query.filter(NotificationTemplate.channel == channel)
        return query.all()

    def get_logs(self, tenant_id: str, channel: Optional[str] = None,
                 skip: int = 0, limit: int = 100) -> List[NotificationLog]:
        query = self.db.query(NotificationLog).filter(
            NotificationLog.tenant_id == tenant_id
        )
        if channel:
            query = query.filter(NotificationLog.channel == channel)
        return query.order_by(NotificationLog.created_at.desc()).offset(skip).limit(limit).all()

    def notify_order_ready(self, order, customer, tenant_id: str):
        """Send order ready notification via multiple channels."""
        results = []

        if customer and customer.phone:
            sms_result = self.send_sms(
                to=customer.phone,
                message=f"Your order {order.order_number} is ready for pickup!",
                tenant_id=tenant_id
            )
            results.append(sms_result)

        if customer and customer.email:
            email_result = self.send_email(
                to=customer.email,
                subject=f"Order {order.order_number} Ready",
                body=f"Dear {customer.name}, your order {order.order_number} is ready for pickup.",
                tenant_id=tenant_id
            )
            results.append(email_result)

        return results
