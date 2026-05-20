from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.modules.order.schemas import OrderCreate, OrderUpdate, OrderResponse
from app.modules.order.repository import OrderRepository
from app.modules.order.events import OrderCreatedEvent, OrderStatusChangedEvent
from app.core.config import tenant_context
from app.infrastructure.messaging import publish
from app.infrastructure.websocket_manager import (
    notify_order_created, notify_order_updated, notify_table_updated
)
from app.models import MenuItem, MenuVariant, MenuModifier, MenuModifierGroup


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)

    def create_order(self, data: OrderCreate) -> dict:
        order_number = self._generate_order_number()

        # Bulk-fetch all menu items, variants, and modifiers to avoid N+1 queries
        item_ids = [item.menu_item_id for item in data.items]
        variant_ids = [item.variant_id for item in data.items if item.variant_id]
        modifier_ids = []
        for item in data.items:
            if item.modifiers:
                for mod_ref in item.modifiers:
                    mod_id = mod_ref.get("id") if isinstance(mod_ref, dict) else mod_ref
                    if mod_id:
                        modifier_ids.append(mod_id)

        menu_items_map = {
            str(mi.id): mi for mi in
            self.db.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
        }
        variants_map = {
            str(v.id): v for v in
            self.db.query(MenuVariant).filter(MenuVariant.id.in_(variant_ids)).all()
        } if variant_ids else {}
        modifiers_map = {
            str(m.id): m for m in
            self.db.query(MenuModifier).filter(MenuModifier.id.in_(modifier_ids)).all()
        } if modifier_ids else {}

        # Calculate item totals with modifier/variant pricing
        subtotal = 0.0
        enriched_items = []

        for item_data in data.items:
            menu_item = menu_items_map.get(item_data.menu_item_id)
            if not menu_item:
                raise ValueError(f"Menu item {item_data.menu_item_id} not found")

            # SECURITY: Always use server-side price from DB, never client-supplied price
            unit_price = float(menu_item.base_price)
            item_total = unit_price * float(item_data.quantity)

            # Add variant price adjustment
            if item_data.variant_id:
                variant = variants_map.get(item_data.variant_id)
                if variant:
                    item_total += float(variant.price_adjustment) * float(item_data.quantity)

            # Add modifier prices
            modifier_total = 0.0
            if item_data.modifiers:
                for mod_ref in item_data.modifiers:
                    mod_id = mod_ref.get("id") if isinstance(mod_ref, dict) else mod_ref
                    if mod_id:
                        modifier = modifiers_map.get(mod_id)
                        if modifier:
                            modifier_total += float(modifier.price) * float(item_data.quantity)

            item_total += modifier_total
            item_tax_rate = float(menu_item.tax_rate) if menu_item.tax_rate else 18.0
            tax_amount = item_total * (item_tax_rate / 100)

            enriched_items.append({
                "id": str(uuid.uuid4()),
                "menu_item_id": item_data.menu_item_id,
                "item_name": item_data.item_name,
                "item_code": item_data.item_code,
                "quantity": item_data.quantity,
                "unit_price": unit_price,
                "tax_amount": round(tax_amount, 2),
                "discount_amount": item_data.discount_amount or 0,
                "total": round(item_total, 2),
                "variant_id": item_data.variant_id,
                "variant_name": item_data.variant_name,
                "modifiers": item_data.modifiers or [],
                "cooking_instructions": item_data.cooking_instructions,
                "course_type": item_data.course_type,
                "prep_status": "pending",
                "priority": item_data.priority or "normal"
            })

            subtotal += item_total

        # Calculate tax using tax config (fallback to 18% if no config)
        tax_amount = self._calculate_tax(subtotal, data.order_type or "dine_in", data.branch_id)
        discount = data.discount_amount or 0
        total = subtotal + tax_amount - discount

        branch_id = data.branch_id or tenant_context.branch_id

        order = {
            "id": str(uuid.uuid4()),
            "order_number": order_number,
            "tenant_id": tenant_context.tenant_id,
            "branch_id": branch_id,
            "table_id": data.table_id,
            "order_type": data.order_type,
            "status": "pending",
            "customer_id": data.customer_id,
            "customer_name": data.customer_name,
            "customer_phone": data.customer_phone,
            "subtotal": round(subtotal, 2),
            "tax_amount": round(tax_amount, 2),
            "discount_amount": round(discount, 2),
            "total": round(total, 2),
            "payment_status": "pending",
            "special_instructions": data.special_instructions,
            "source": data.source or "pos",
            "created_by": tenant_context.user_id,
        }

        result = self.repo.create_order_with_items(order, enriched_items)

        # Update table's current_order_id if table specified
        if data.table_id:
            from app.models import DiningTable
            table = self.db.query(DiningTable).filter(DiningTable.id == data.table_id).first()
            if table:
                table.current_order_id = order["id"]
                self.db.commit()

        # Publish event
        event = OrderCreatedEvent(
            order_id=order["id"],
            order_number=order_number,
            tenant_id=tenant_context.tenant_id,
            branch_id=branch_id,
            total=total
        )
        self._publish_event(event)

        # WebSocket notification for real-time updates
        try:
            import asyncio
            order_ws_data = {
                "id": order["id"],
                "order_number": order_number,
                "order_type": data.order_type,
                "table_id": data.table_id,
                "status": "pending",
                "items": enriched_items,
                "total": round(total, 2),
                "source": data.source or "pos",
            }
            asyncio.create_task(notify_order_created(
                tenant_context.tenant_id, branch_id, order_ws_data
            ))
            if data.table_id:
                asyncio.create_task(notify_table_updated(
                    tenant_context.tenant_id, branch_id,
                    {"id": data.table_id, "current_order_id": order["id"], "status": "occupied"}
                ))
        except Exception:
            pass  # Don't fail order creation if WS notification fails

        return result

    def update_status(self, order_id: str, new_status: str) -> dict:
        order = self.repo.get_order(order_id)
        if not order:
            raise ValueError("Order not found")

        old_status = order.status
        result = self.repo.update_order_status(order_id, new_status)

        # Clear table if order completed/cancelled
        if new_status in ("completed", "cancelled"):
            from app.models import DiningTable
            table = self.db.query(DiningTable).filter(DiningTable.current_order_id == order_id).first()
            if table:
                table.current_order_id = None
                self.db.commit()

        event = OrderStatusChangedEvent(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=tenant_context.user_id
        )
        self._publish_event(event)

        # WebSocket notification for real-time updates
        try:
            import asyncio
            asyncio.create_task(notify_order_updated(
                tenant_context.tenant_id,
                order.branch_id if hasattr(order, 'branch_id') else tenant_context.branch_id,
                {"id": order_id, "status": new_status, "old_status": old_status}
            ))
            if new_status in ("completed", "cancelled"):
                table = self.db.query(DiningTable).filter(DiningTable.current_order_id == order_id).first()
                if table:
                    asyncio.create_task(notify_table_updated(
                        tenant_context.tenant_id,
                        order.branch_id if hasattr(order, 'branch_id') else tenant_context.branch_id,
                        {"id": str(table.id), "current_order_id": None, "status": "free"}
                    ))
        except Exception:
            pass

        if new_status == "ready":
            self._notify_customer(order_id)

        return result

    def get_active_orders(self, branch_id: Optional[str] = None) -> list:
        filters = {}
        if branch_id:
            filters["branch_id"] = branch_id
        else:
            filters["tenant_id"] = tenant_context.tenant_id
        return self.repo.get_orders_by_status(
            filters=filters,
            statuses=["pending", "confirmed", "preparing", "ready"]
        )

    def _calculate_tax(self, subtotal: float, order_type: str, branch_id: Optional[str]) -> float:
        """Calculate tax using TaxConfig if available, fallback to 18%."""
        try:
            from app.modules.tax.service import TaxService
            tax_service = TaxService(self.db)
            result = tax_service.calculate_tax(
                tenant_id=tenant_context.tenant_id,
                subtotal=subtotal,
                order_type=order_type,
                branch_id=branch_id
            )
            return result["total_tax"]
        except Exception:
            # Fallback to 18% if tax config fails
            return subtotal * 0.18

    def _generate_order_number(self) -> str:
        """Generate a unique order number.

        Uses date prefix + short UUID suffix to avoid race conditions
        that occur with sequential counting under concurrent requests.
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:8].upper()
        return f"ORD-{today}-{short_id}"

    def _publish_event(self, event):
        try:
            publish("order_events", event.dict())
        except Exception:
            pass  # Don't fail order creation if event publishing fails

    def _notify_customer(self, order_id: str):
        try:
            from app.workers.tasks.notification_tasks import send_order_ready_notification
            send_order_ready_notification.delay(order_id)
        except Exception:
            pass  # Don't fail if notification fails
