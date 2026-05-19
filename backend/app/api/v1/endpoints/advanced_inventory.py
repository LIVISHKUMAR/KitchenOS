"""Advanced inventory endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.inventory.advanced import AdvancedInventoryService

router = APIRouter()


class WasteLog(BaseModel):
    inventory_item_id: str
    quantity: float
    reason: str


class UnitConversion(BaseModel):
    quantity: float
    from_unit: str
    to_unit: str


@router.post("/waste")
async def log_waste(
    data: WasteLog,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedInventoryService(db)
    return service.log_waste(
        inventory_item_id=data.inventory_item_id,
        quantity=data.quantity,
        reason=data.reason,
        branch_id=current_user.get("branch_id", ""),
        user_id=current_user["user_id"]
    )


@router.get("/waste-report")
async def waste_report(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedInventoryService(db)
    return service.get_waste_report(current_user["tenant_id"], branch_id)


@router.get("/valuation")
async def stock_valuation(
    branch_id: Optional[str] = None,
    method: str = "weighted_avg",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedInventoryService(db)
    return service.get_stock_valuation(current_user["tenant_id"], branch_id, method)


@router.get("/batches/{item_id}")
async def batch_info(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedInventoryService(db)
    return service.get_batch_info(item_id)


@router.post("/convert-unit")
async def convert_unit(
    data: UnitConversion,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    service = AdvancedInventoryService(db)
    result = service.convert_unit(data.quantity, data.from_unit, data.to_unit)
    return {"original": data.quantity, "from_unit": data.from_unit,
            "converted": result, "to_unit": data.to_unit}
