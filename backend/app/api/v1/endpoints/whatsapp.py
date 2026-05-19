"""WhatsApp messaging endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.whatsapp.service import whatsapp_service

router = APIRouter()


class SendMessage(BaseModel):
    to: str
    message: str


class OrderNotification(BaseModel):
    phone: str
    order_number: str
    total: float
    items: list = []


@router.post("/send")
async def send_message(
    data: SendMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send a WhatsApp message."""
    result = await whatsapp_service.send_message(data.to, data.message)
    return result


@router.post("/order-confirmation")
async def order_confirmation(
    data: OrderNotification,
    current_user: dict = Depends(get_current_user)
):
    """Send order confirmation via WhatsApp."""
    result = await whatsapp_service.send_order_confirmation(
        data.phone, data.order_number, data.total, data.items
    )
    return result


@router.post("/order-ready")
async def order_ready(
    phone: str,
    order_number: str,
    current_user: dict = Depends(get_current_user)
):
    """Send order ready notification."""
    result = await whatsapp_service.send_order_ready(phone, order_number)
    return result


@router.post("/feedback-request")
async def feedback_request(
    phone: str,
    order_number: str,
    current_user: dict = Depends(get_current_user)
):
    """Send feedback request."""
    result = await whatsapp_service.send_feedback_request(phone, order_number)
    return result
