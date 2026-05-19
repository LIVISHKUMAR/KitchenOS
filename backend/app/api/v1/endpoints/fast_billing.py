"""Fast billing endpoints for optimized POS workflow."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.order.fast_billing import FastBillingEngine

router = APIRouter()


class QuickOrderRequest(BaseModel):
    order_type: str = "dine_in"
    table_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: list  # [{menu_item_id, quantity, cooking_instructions?, modifiers?}]
    discount_amount: float = 0
    source: str = "pos"


class QuickPayRequest(BaseModel):
    payment_method: str  # cash, card, upi
    amount: Optional[float] = None
    open_drawer: bool = False


@router.post("/quick-order")
async def quick_order(
    data: QuickOrderRequest,
    idempotency_key: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create an order in a single optimized call.

    This is the fastest path for billing:
    1. Creates order
    2. Calculates tax
    3. Generates KOT
    4. Returns everything needed for bill printing

    Use idempotency-key header to prevent duplicate orders.
    """
    engine = FastBillingEngine(db)
    result = engine.quick_order(data.model_dump(), idempotency_key)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/quick-pay/{order_id}")
async def quick_pay(
    order_id: str,
    data: QuickPayRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Process payment in a single call.

    1. Records payment
    2. Updates order status
    3. Clears table
    4. Prints bill
    5. Opens cash drawer (if cash payment)
    """
    engine = FastBillingEngine(db)
    result = engine.quick_pay(
        order_id=order_id,
        payment_method=data.payment_method,
        amount=data.amount,
        open_drawer=data.open_drawer
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
