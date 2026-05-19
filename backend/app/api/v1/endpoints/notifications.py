"""Notification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.notification.service import NotificationService

router = APIRouter()


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class SMSRequest(BaseModel):
    to: str
    message: str


class PushRequest(BaseModel):
    user_id: str
    title: str
    body: str


class TemplateCreate(BaseModel):
    name: str
    channel: str  # email, sms, push
    event: str
    subject: str = ""
    body: str


@router.post("/email")
async def send_email(
    data: EmailRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.send_email(
        to=data.to,
        subject=data.subject,
        body=data.body,
        tenant_id=current_user["tenant_id"]
    )


@router.post("/sms")
async def send_sms(
    data: SMSRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.send_sms(
        to=data.to,
        message=data.message,
        tenant_id=current_user["tenant_id"]
    )


@router.post("/push")
async def send_push(
    data: PushRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.send_push(
        user_id=data.user_id,
        title=data.title,
        body=data.body,
        tenant_id=current_user["tenant_id"]
    )


@router.post("/templates")
async def create_template(
    data: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.create_template(
        tenant_id=current_user["tenant_id"],
        name=data.name,
        channel=data.channel,
        event=data.event,
        subject=data.subject,
        body=data.body
    )


@router.get("/templates")
async def list_templates(
    channel: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.get_templates(current_user["tenant_id"], channel)


@router.get("/logs")
async def list_notification_logs(
    channel: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    notification_service = NotificationService(db)
    return notification_service.get_logs(
        current_user["tenant_id"], channel, skip=skip, limit=limit
    )
