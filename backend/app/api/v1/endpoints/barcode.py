"""Barcode and QR code endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.barcode.service import BarcodeService

router = APIRouter()


class BarcodeAssign(BaseModel):
    item_type: str  # menu, inventory
    item_id: str
    barcode: str = None


@router.get("/lookup/{barcode}")
async def lookup_barcode(
    barcode: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = BarcodeService(db)
    return service.lookup_by_barcode(barcode, current_user["tenant_id"])


@router.post("/assign")
async def assign_barcode(
    data: BarcodeAssign,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = BarcodeService(db)
    return service.assign_barcode_to_item(data.item_type, data.item_id, data.barcode)


@router.get("/qr/{entity_type}/{entity_id}")
async def generate_qr(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = BarcodeService(db)
    return service.generate_qr_data(entity_type, entity_id, current_user.get("branch_id"))
