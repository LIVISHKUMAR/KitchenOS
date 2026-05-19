from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.order.service import OrderService
from app.modules.order.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
)
from app.models import Order

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    if not order.branch_id:
        order.branch_id = current_user.get("branch_id")
    return order_service.create_order(order)


@router.get("/", response_model=List[OrderResponse])
async def read_orders(
    branch_id: Optional[str] = None,
    order_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    if order_status:
        filters = {"tenant_id": current_user["tenant_id"]}
        if branch_id:
            filters["branch_id"] = branch_id
        return order_service.repo.get_orders_by_status(filters=filters, statuses=[order_status])
    return order_service.get_active_orders(branch_id=branch_id)


@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    order = order_service.repo.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["tenant_id"] != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = order_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Handle status change separately for event publishing
    if "status" in update_data:
        new_status = update_data.pop("status")
        result = order_service.update_status(order_id, new_status)
        # Apply remaining updates
        if update_data:
            for key, value in update_data.items():
                setattr(db_order, key, value)
            db_order.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_order)
            result = order_service.repo.get_order_with_items(order_id)
        return result

    # Apply non-status updates
    for key, value in update_data.items():
        setattr(db_order, key, value)
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return order_service.repo.get_order_with_items(order_id)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Soft delete — use service to handle table cleanup
    order_service.update_status(order_id, "cancelled")
    return None


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    new_status: str = Query(..., alias="status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    valid_statuses = ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    return order_service.update_status(order_id, new_status)


@router.get("/active/", response_model=List[OrderResponse])
async def get_active_orders(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    order_service = OrderService(db)
    return order_service.get_active_orders(branch_id=branch_id)
