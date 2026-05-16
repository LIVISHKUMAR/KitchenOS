from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.payment.service import PaymentService
from app.modules.payment.schemas import (
    PaymentCreate, PaymentUpdate, PaymentResponse
)

router = APIRouter()

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new payment.
    """
    payment_service = PaymentService(db)
    payment.tenant_id = current_user["tenant_id"]
    payment.branch_id = current_user.get("branch_id")
    return payment_service.create_payment(payment.dict())

@router.get("/", response_model=List[PaymentResponse])
async def read_payments(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve payments.
    """
    payment_service = PaymentService(db)
    return payment_service.get_payments(
        tenant_id=current_user["tenant_id"],
        skip=skip,
        limit=limit
    )

@router.get("/{payment_id}", response_model=PaymentResponse)
async def read_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific payment by ID.
    """
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    # Check tenant access
    if payment.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return payment

@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update a specific payment.
    """
    payment_service = PaymentService(db)
    # Check tenant access
    db_payment = payment_service.get_payment(payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if db_payment.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_payment = payment_service.update_payment(payment_id, payment.dict(exclude_unset=True))
    if not updated_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return updated_payment

@router.get("/order/{order_id}", response_model=List[PaymentResponse])
async def read_payments_by_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve payments for a specific order.
    """
    payment_service = PaymentService(db)
    # In a full implementation, we'd verify the order belongs to the tenant
    return payment_service.get_payments_by_order(order_id)
