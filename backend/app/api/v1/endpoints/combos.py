"""Combo/meal endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.order.combo import ComboService

router = APIRouter()


class ComboSelection(BaseModel):
    combo_item_id: str
    selected_items: List[dict]  # [{menu_item_id, variant_id?}]


@router.post("/calculate-price")
async def calculate_combo_price(
    data: ComboSelection,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    combo_service = ComboService(db)
    return combo_service.calculate_combo_price(data.combo_item_id, data.selected_items)


@router.post("/validate")
async def validate_combo(
    data: ComboSelection,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    combo_service = ComboService(db)
    return combo_service.validate_combo_selection(data.combo_item_id, data.selected_items)
