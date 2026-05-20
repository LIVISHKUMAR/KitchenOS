from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.modules.auth.rbac import require_permission
from app.infrastructure.database import get_db_session
from app.modules.payment.service import PaymentService
from app.modules.payment.schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from app.infrastructure.websocket_manager import notify_payment_completed

router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    current_user: dict = Depends(require_permission("payment:create")),
    db: Session = Depends(get_db_session)
):
    payment_service = PaymentService(db)
    payment_data = payment.model_dump()
    payment_data["tenant_id"] = current_user["tenant_id"]
    payment_data["branch_id"] = current_user.get("branch_id")
    result = payment_service.create_payment(payment_data)

    # WebSocket notification for real-time updates
    try:
        import asyncio
        asyncio.create_task(notify_payment_completed(
            current_user["tenant_id"],
            current_user.get("branch_id"),
            {
                "id": str(result.id) if hasattr(result, 'id') else str(result.get('id', '')),
                "order_id": str(payment.order_id),
                "amount": float(payment.amount),
                "payment_method": payment.payment_method,
            }
        ))
    except Exception:
        pass

    return result


@router.get("/", response_model=List[PaymentResponse])
async def read_payments(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
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
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if str(payment.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    payment_service = PaymentService(db)
    db_payment = payment_service.get_payment(payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if str(db_payment.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_payment = payment_service.update_payment(payment_id, payment.model_dump(exclude_unset=True))
    if not updated_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return updated_payment


@router.get("/order/{order_id}", response_model=List[PaymentResponse])
async def read_payments_by_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    payment_service = PaymentService(db)
    return payment_service.get_payments_by_order(order_id)


class RefundRequest(BaseModel):
    payment_id: str
    amount: float
    reason: str


@router.post("/refund")
async def create_refund(
    data: RefundRequest,
    current_user: dict = Depends(require_permission("payment:create")),
    db: Session = Depends(get_db_session)
):
    """Create a refund for a payment."""
    from app.models import Payment
    import uuid

    original = db.query(Payment).filter(Payment.id == data.payment_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Original payment not found")
    if str(original.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if data.amount > float(original.amount):
        raise HTTPException(status_code=400, detail="Refund exceeds original amount")

    refund = Payment(
        id=str(uuid.uuid4()),
        order_id=original.order_id,
        tenant_id=original.tenant_id,
        branch_id=original.branch_id,
        amount=-abs(data.amount),
        payment_method=original.payment_method,
        status="refunded",
        refund_id=original.id,
        refund_amount=data.amount,
        refund_reason=data.reason,
    )
    db.add(refund)
    original.status = "partially_refunded" if data.amount < float(original.amount) else "refunded"
    db.commit()
    db.refresh(refund)

    return {
        "id": str(refund.id),
        "original_payment_id": data.payment_id,
        "refund_amount": data.amount,
        "reason": data.reason,
        "status": "refunded",
        "message": "Refund processed successfully",
    }


class VoidRequest(BaseModel):
    reason: str


@router.post("/{payment_id}/void")
async def void_payment(
    payment_id: str,
    data: VoidRequest,
    current_user: dict = Depends(require_permission("payment:create")),
    db: Session = Depends(get_db_session)
):
    """Void a payment (cancel before settlement)."""
    from app.models import Payment

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if str(payment.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if payment.status in ("refunded", "voided"):
        raise HTTPException(status_code=400, detail="Payment already refunded/voided")

    payment.status = "voided"
    payment.refund_reason = data.reason
    db.commit()

    return {"id": payment_id, "status": "voided", "reason": data.reason, "message": "Payment voided"}
