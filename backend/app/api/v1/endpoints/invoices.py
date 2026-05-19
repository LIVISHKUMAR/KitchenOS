"""Invoice generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.invoice.service import InvoiceService
from app.models import Order

router = APIRouter()


@router.get("/{order_id}")
async def get_invoice(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate GST invoice for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    invoice_service = InvoiceService(db)
    return invoice_service.generate_invoice(order_id)
