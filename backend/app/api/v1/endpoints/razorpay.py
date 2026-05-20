"""Razorpay payment gateway endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.payment.razorpay import razorpay_gateway

router = APIRouter()


class RazorpayOrderRequest(BaseModel):
    amount: float
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[dict] = None


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
async def create_razorpay_order(
    data: RazorpayOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a Razorpay order for payment."""
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    try:
        result = razorpay_gateway.create_order(
            amount=data.amount,
            currency=data.currency,
            receipt=data.receipt,
            notes=data.notes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_razorpay_payment(
    data: RazorpayVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verify Razorpay payment signature."""
    is_valid = razorpay_gateway.verify_payment(
        razorpay_order_id=data.razorpay_order_id,
        razorpay_payment_id=data.razorpay_payment_id,
        razorpay_signature=data.razorpay_signature,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    return {"verified": True, "payment_id": data.razorpay_payment_id}
