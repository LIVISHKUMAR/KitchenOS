from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.inventory.service import InventoryService
from app.modules.inventory.schemas import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    StockMovementCreate, StockMovementUpdate, StockMovementResponse
)

router = APIRouter()

@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item: InventoryItemCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new inventory item.
    """
    inventory_service = InventoryService(db)
    item.tenant_id = current_user["tenant_id"]
    item.branch_id = current_user.get("branch_id")
    return inventory_service.create_inventory_item(item.dict())

@router.get("/items", response_model=List[InventoryItemResponse])
async def read_inventory_items(
    branch_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve inventory items.
    """
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
    """
    Retrieve a specific inventory item by ID.
    """
    inventory_service = InventoryService(db)
    item = inventory_service.get_inventory_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    # Check tenant access
    if item.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return item

@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item: InventoryItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update a specific inventory item.
    """
    inventory_service = InventoryService(db)
    # Check tenant access
    db_item = inventory_service.get_inventory_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_item = inventory_service.update_inventory_item(item_id, item.dict(exclude_unset=True))
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete a specific inventory item.
    """
    inventory_service = InventoryService(db)
    # Check tenant access
    db_item = inventory_service.get_inventory_item(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.tenant_id != current_user["tenant_id"]:
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
    """
    Retrieve low stock inventory items.
    """
    inventory_service = InventoryService(db)
    return inventory_service.get_low_stock_items(
        tenant_id=current_user["tenant_id"],
        branch_id=branch_id
    )

# Stock movement endpoints
@router.post("/stock-movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    movement: StockMovementCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new stock movement.
    """
    # In a full implementation, this would have its own service
    # For now, we'll return a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Stock movement endpoint not fully implemented"
    )
