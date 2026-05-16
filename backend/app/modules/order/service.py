from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import uuid

from app.modules.order.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
)
from app.modules.order.repository import OrderRepository
from app.modules.order.events import OrderCreatedEvent, OrderStatusChangedEvent
from app.core.config import tenant_context

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)
    
    def create_order(self, data: OrderCreate) -> OrderResponse:
        # Generate order number
        order_number = self._generate_order_number()
        
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in data.items)
        tax_amount = subtotal * 0.18  # 18% GST
        total = subtotal + tax_amount - (data.discount_amount or 0)
        
        order = {
            "id": str(uuid.uuid4()),
            "order_number": order_number,
            "tenant_id": tenant_context.tenant_id,
            "branch_id": data.branch_id or tenant_context.branch_id,
            "table_id": data.table_id,
            "order_type": data.order_type,
            "status": "pending",
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total": total,
            "customer_id": data.customer_id,
            "created_by": tenant_context.user_id,
        }
        
        # Create order items
        order_items = []
        for item_data in data.items:
            order_items.append({
                "id": str(uuid.uuid4()),
                "menu_item_id": item_data.menu_item_id,
                "item_name": item_data.item_name,
                "quantity": item_data.quantity,
                "unit_price": item_data.unit_price,
                "total": item_data.unit_price * item_data.quantity,
            })
        
        result = self.repo.create_order_with_items(order, order_items)
        
        # Publish domain event (async via RabbitMQ)
        self._publish_event(OrderCreatedEvent(
            order_id=result["id"],
            order_number=order_number,
            tenant_id=order["tenant_id"],
            branch_id=order["branch_id"],
            total=total
        ))
        
        return result
    
    def update_status(self, order_id: str, new_status: str) -> OrderResponse:
        current = self.repo.get_order(order_id)
        if not current:
            raise ValueError("Order not found")
        
        old_status = current.status
        result = self.repo.update_order_status(order_id, new_status)
        
        # Publish status change event
        self._publish_event(OrderStatusChangedEvent(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=tenant_context.user_id
        ))
        
        # Trigger notifications based on status
        if new_status == "ready":
            self._notify_customer(order_id)
        
        return result
    
    def get_active_orders(self, branch_id: str = None) -> List[OrderResponse]:
        filters = {"tenant_id": tenant_context.tenant_id}
        if branch_id:
            filters["branch_id"] = branch_id
        
        return self.repo.get_orders_by_status(
            filters=filters,
            statuses=["pending", "confirmed", "preparing"]
        )
    
    def _generate_order_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        count = self.repo.get_today_order_count(tenant_context.tenant_id)
        return f"ORD-{today}-{count + 1:04d}"
    
    def _publish_event(self, event):
        # Async publish to RabbitMQ
        from app.infrastructure.messaging import publish
        publish("order_events", event.dict())
    
    def _notify_customer(self, order_id: str):
        from app.workers.tasks.notification_tasks import send_order_ready_notification
        send_order_ready_notification.delay(order_id)