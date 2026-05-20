from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.modules.auth.rbac import require_permission
from app.infrastructure.database import get_db_session
from app.modules.inventory.service import InventoryService
from app.modules.inventory.schemas import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    StockMovementCreate, StockMovementResponse
)
from app.models import StockMovement
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item: InventoryItemCreate,
    current_user: dict = Depends(require_permission("inventory:create")),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    item_data = item.model_dump()
    item_data["tenant_id"] = current_user["tenant_id"]
    item_data["branch_id"] = current_user.get("branch_id")
    return inventory_service.create_inventory_item(item_data)


@router.get("/items", response_model=List[InventoryItemResponse])
async def read_inventory_items(
    branch_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    return inventory_service.get_inventory_items(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id,
        skip=skip,
        limit=limit
    )


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def read_inventory_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    item = inventory_service.get_inventory_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return item


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item: InventoryItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    db_item = inventory_service.get_inventory_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(db_item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_item = inventory_service.update_inventory_item(item_id, item.model_dump(exclude_unset=True))
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    db_item = inventory_service.get_inventory_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if str(db_item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    success = inventory_service.delete_inventory_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return None


@router.get("/low-stock", response_model=List[InventoryItemResponse])
async def get_low_stock_items(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    inventory_service = InventoryService(db)
    return inventory_service.get_low_stock_items(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id
    )


@router.post("/stock-movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    movement: StockMovementCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    db_movement = StockMovement(
        id=str(uuid.uuid4()),
        inventory_item_id=movement.inventory_item_id,
        branch_id=movement.branch_id or current_user.get("branch_id"),
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        reference_type=movement.reference_type,
        reference_id=movement.reference_id,
        batch_number=movement.batch_number,
        expiry_date=movement.expiry_date,
        notes=movement.notes,
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    db.add(db_movement)

    # Update inventory stock based on movement type
    inventory_service = InventoryService(db)
    item = inventory_service.get_inventory_item(movement.inventory_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if str(item.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if movement.movement_type in ("purchase", "return", "adjustment_in"):
        item.current_stock = float(item.current_stock) + float(movement.quantity)
    elif movement.movement_type in ("sale", "waste", "transfer", "adjustment_out"):
        item.current_stock = float(item.current_stock) - float(movement.quantity)

    db.commit()
    db.refresh(db_movement)
    return db_movement
