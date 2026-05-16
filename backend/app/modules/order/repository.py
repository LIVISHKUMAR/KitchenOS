from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import Order, OrderItem
import uuid
from datetime import datetime

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_order_with_items(self, order: dict, order_items: List[dict]) -> dict:
        db_order = Order(**order)
        self.db.add(db_order)
        self.db.flush()  # Get the ID without committing
        
        # Create order items
        for item_data in order_items:
            item_data["order_id"] = db_order.id
            db_item = OrderItem(**item_data)
            self.db.add(db_item)
        
        self.db.commit()
        self.db.refresh(db_order)
        
        # Return the order with items
        return self.get_order_with_items(str(db_order.id))
    
    def get_order(self, order_id: str) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_order_with_items(self, order_id: str) -> Optional[dict]:
        order = self.get_order(order_id)
        if not order:
            return None
        
        # Get order items
        items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        # Convert to dict format
        order_dict = {
            "id": str(order.id),
            "order_number": order.order_number,
            "tenant_id": str(order.tenant_id),
            "branch_id": str(order.branch_id),
            "table_id": str(order.table_id) if order.table_id else None,
            "order_type": order.order_type,
            "status": order.status,
            "customer_id": str(order.customer_id) if order.customer_id else None,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "discount_amount": float(order.discount_amount),
            "tip_amount": float(order.tip_amount),
            "total": float(order.total),
            "payment_status": order.payment_status,
            "special_instructions": order.special_instructions,
            "source": order.source,
            "delivery_address": order.delivery_address,
            "delivery_partner": order.delivery_partner,
            "aggregator_order_id": order.aggregator_order_id,
            "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            "created_by": str(order.created_by) if order.created_by else None,
            "assigned_to": str(order.assigned_to) if order.assigned_to else None,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "items": [
                {
                    "id": str(item.id),
                    "menu_item_id": str(item.menu_item_id),
                    "item_name": item.item_name,
                    "item_code": item.item_code,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "tax_amount": float(item.tax_amount),
                    "discount_amount": float(item.discount_amount),
                    "total": float(item.total),
                    "variant_id": str(item.variant_id) if item.variant_id else None,
                    "variant_name": item.variant_name,
                    "modifiers": item.modifiers,
                    "cooking_instructions": item.cooking_instructions,
                    "course_type": item.course_type,
                    "prep_status": item.prep_status,
                    "prep_started_at": item.prep_started_at.isoformat() if item.prep_started_at else None,
                    "ready_at": item.ready_at.isoformat() if item.ready_at else None,
                    "served_at": item.served_at.isoformat() if item.served_at else None,
                    "priority": item.priority,
                    "created_at": item.created_at.isoformat()
                }
                for item in items
            ]
        }
        
        return order_dict
    
    def update_order_status(self, order_id: str, new_status: str) -> dict:
        order = self.get_order(order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
            return self.get_order_with_items(order_id)
        return None
    
    def get_orders_by_status(self, filters: dict, statuses: List[str]) -> List[dict]:
        query = self.db.query(Order)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(Order, key):
                query = query.filter(getattr(Order, key) == value)
        
        # Filter by status
        query = query.filter(Order.status.in_(statuses))
        
        orders = query.all()
        
        # Convert to dict format
        return [
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "tenant_id": str(order.tenant_id),
                "branch_id": str(order.branch_id),
                "table_id": str(order.table_id) if order.table_id else None,
                "order_type": order.order_type,
                "status": order.status,
                "customer_id": str(order.customer_id) if order.customer_id else None,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "subtotal": float(order.subtotal),
                "tax_amount": float(order.tax_amount),
                "discount_amount": float(order.discount_amount),
                "tip_amount": float(order.tip_amount),
                "total": float(order.total),
                "payment_status": order.payment_status,
                "special_instructions": order.special_instructions,
                "source": order.source,
                "delivery_address": order.delivery_address,
                "delivery_partner": order.delivery_partner,
                "aggregator_order_id": order.aggregator_order_id,
                "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
                "created_by": str(order.created_by) if order.created_by else None,
                "assigned_to": str(order.assigned_to) if order.assigned_to else None,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
            for order in orders
        ]
    
    def get_today_order_count(self, tenant_id: str) -> int:
        today = datetime.utcnow().date()
        return self.db.query(Order).filter(
            Order.tenant_id == tenant_id,
            func.date(Order.created_at) == today
        ).count()