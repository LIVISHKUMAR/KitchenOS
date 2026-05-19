"""QR code endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.qr.service import QRService

router = APIRouter()


@router.get("/table/{table_id}")
async def generate_table_qr(
    table_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = QRService(db)
    return service.generate_table_qr(table_id)


@router.get("/menu/{branch_id}")
async def generate_menu_qr(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = QRService(db)
    return service.generate_menu_qr(branch_id)


@router.get("/menu-for-table/{table_id}")
async def get_menu_for_table(
    table_id: str,
    db: Session = Depends(get_db_session)
):
    """Public endpoint - no auth required for QR ordering."""
    service = QRService(db)
    return service.get_menu_for_table(table_id)
