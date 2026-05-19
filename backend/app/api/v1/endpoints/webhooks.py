"""Webhook management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.webhook.service import WebhookService

router = APIRouter()


class WebhookCreate(BaseModel):
    url: str
    events: list  # ["order.created", "payment.completed", ...]
    description: str = ""


class WebhookResponse(BaseModel):
    id: str
    tenant_id: str
    url: str
    secret: str
    events: list
    is_active: bool
    description: str

    class Config:
        from_attributes = True


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    webhook_service = WebhookService(db)
    return webhook_service.create_webhook(
        tenant_id=current_user["tenant_id"],
        url=webhook.url,
        events=webhook.events,
        description=webhook.description
    )


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    webhook_service = WebhookService(db)
    return webhook_service.get_webhooks(current_user["tenant_id"])


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    webhook_service = WebhookService(db)
    if not webhook_service.delete_webhook(webhook_id, current_user["tenant_id"]):
        raise HTTPException(status_code=404, detail="Webhook not found")
    return None


@router.get("/{webhook_id}/deliveries")
async def list_deliveries(
    webhook_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    webhook_service = WebhookService(db)
    return webhook_service.get_deliveries(webhook_id, skip=skip, limit=limit)
