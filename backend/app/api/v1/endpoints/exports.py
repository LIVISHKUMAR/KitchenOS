"""Data export endpoints."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.export.service import ExportService

router = APIRouter()


@router.get("/orders")
async def export_orders(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export orders as CSV."""
    export_service = ExportService(db)
    csv_data = export_service.export_orders(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"}
    )


@router.get("/order-items")
async def export_order_items(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export order items as CSV."""
    export_service = ExportService(db)
    csv_data = export_service.export_order_items(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=order_items.csv"}
    )


@router.get("/customers")
async def export_customers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export customers as CSV."""
    export_service = ExportService(db)
    csv_data = export_service.export_customers(current_user["tenant_id"])
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers.csv"}
    )


@router.get("/inventory")
async def export_inventory(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export inventory as CSV."""
    export_service = ExportService(db)
    csv_data = export_service.export_inventory(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id
    )
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"}
    )


@router.get("/payments")
async def export_payments(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Export payments as CSV."""
    export_service = ExportService(db)
    csv_data = export_service.export_payments(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to
    )
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=payments.csv"}
    )
