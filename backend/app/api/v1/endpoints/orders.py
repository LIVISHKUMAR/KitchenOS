from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_current_user
from app.infrastructure.database import get_db_session
from app.modules.order.service import OrderService
from app.modules.order.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
)

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new order.
    """
    order_service = OrderService(db)
    # Set tenant context from current user
    from app.core.config import tenant_context
    tenant_context.set(
        tenant_id=current_user["tenant_id"],
        branch_id=current_user.get("branch_id"),
        user_id=current_user["user_id"]
    )
    
    # Set branch_id from current user if not provided
    if not order.branch_id:
        order.branch_id = current_user.get("branch_id")
    
    return order_service.create_order(order)

@router.get("/", response_model=List[OrderResponse])
async def read_orders(
    branch_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve orders.
    """
    order_service = OrderService(db)
    # For simplicity, we're just getting active orders
    # In a full implementation, we'd have more filtering options
    return order_service.get_active_orders(branch_id=branch_id)

@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific order by ID.
    """
    order_service = OrderService(db)
    # In a full implementation, we'd check tenant access
    order = order_service.repo.get_order_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Check tenant access
    if order["tenant_id"] != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return order

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update a specific order.
    """
    order_service = OrderService(db)
    # Check tenant access
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a full implementation, we'd update the order
    # For now, we'll just return the existing order
    return order_service.repo.get_order_with_items(order_id)

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete a specific order.
    """
    order_service = OrderService(db)
    # Check tenant access
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a full implementation, we'd delete the order
    # For now, we'll just return 204
    return None

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update order status.
    """
    order_service = OrderService(db)
    # Check tenant access
    db_order = order_service.repo.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(db_order.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Valid status transitions
    valid_statuses = ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    return order_service.update_status(order_id, status)

@router.get("/active/", response_model=List[OrderResponse])
async def get_active_orders(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get active orders (pending, confirmed, preparing).
    """
    order_service = OrderService(db)
    return order_service.get_active_orders(branch_id=branch_id)