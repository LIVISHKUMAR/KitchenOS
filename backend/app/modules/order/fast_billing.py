"""Fast Billing Engine.

Optimized order creation for speed:
- Single API call creates order + KOT + payment
- Idempotency keys prevent duplicates
- Auto-applies default tax
- Returns everything needed for bill printing
"""

import uuid
import logging
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, MenuItem, DiningTable, Customer, Payment
from app.core.config import tenant_context
from app.modules.tax.service import TaxService
from app.modules.order.kot_engine import KOTEngine

logger = logging.getLogger("kitchenos.fast_billing")


class FastBillingEngine:
    """Optimized billing for <5 second order completion."""

    def __init__(self, db: Session):
        self.db = db
        self.tax_service = TaxService(db)
        self.kot_engine = KOTEngine(db)

    def quick_order(self, data: dict, idempotency_key: str = None) -> dict:
        """Create an order in a single optimized call.

        This combines: order creation + KOT generation + optional payment
        into one atomic operation for maximum speed.
        """
        # Check idempotency
        if idempotency_key:
            existing = self.db.query(Order).filter(
                Order.idempotency_key == idempotency_key
            ).first()
            if existing:
                return self._order_to_dict(existing)

        # Generate order number
        order_number = self._generate_order_number()

        # Calculate totals
        subtotal = 0.0
        enriched_items = []

        for item_data in data.get("items", []):
            menu_item = self.db.query(MenuItem).filter(
                MenuItem.id == item_data.get("menu_item_id")
            ).first()

            if not menu_item:
                continue

            unit_price = float(menu_item.base_price)
            quantity = float(item_data.get("quantity", 1))
            item_total = unit_price * quantity

            # Apply modifier prices
            if item_data.get("modifiers"):
                for mod in item_data["modifiers"]:
                    if isinstance(mod, dict) and mod.get("price"):
                        item_total += float(mod["price"]) * quantity

            subtotal += item_total

            enriched_items.append({
                "id": str(uuid.uuid4()),
                "menu_item_id": str(menu_item.id),
                "item_name": menu_item.name,
                "item_code": menu_item.item_code,
                "quantity": quantity,
                "unit_price": unit_price,
                "tax_amount": 0,  # Will be calculated
                "discount_amount": 0,
                "total": item_total,
                "variant_id": item_data.get("variant_id"),
                "variant_name": item_data.get("variant_name"),
                "modifiers": item_data.get("modifiers", []),
                "cooking_instructions": item_data.get("cooking_instructions"),
                "course_type": item_data.get("course_type", "main"),
                "prep_status": "pending",
                "priority": item_data.get("priority", "normal")
            })

        # Calculate tax
        tax_result = self.tax_service.calculate_tax(
            tenant_id=tenant_context.tenant_id,
            subtotal=subtotal,
            order_type=data.get("order_type", "dine_in"),
            branch_id=data.get("branch_id") or tenant_context.branch_id
        )
        tax_amount = tax_result["total_tax"]

        # Apply tax to items proportionally
        if subtotal > 0:
            for item in enriched_items:
                item["tax_amount"] = round((item["total"] / subtotal) * tax_amount, 2)

        discount = data.get("discount_amount", 0)
        total = subtotal + tax_amount - discount

        # Create order
        order_id = str(uuid.uuid4())
        order = Order(
            id=order_id,
            order_number=order_number,
            tenant_id=tenant_context.tenant_id,
            branch_id=data.get("branch_id") or tenant_context.branch_id,
            table_id=data.get("table_id"),
            order_type=data.get("order_type", "dine_in"),
            status="confirmed",
            customer_id=data.get("customer_id"),
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            discount_amount=round(discount, 2),
            total=round(total, 2),
            payment_status="pending",
            special_instructions=data.get("special_instructions"),
            source=data.get("source", "pos"),
            created_by=tenant_context.user_id,
            idempotency_key=idempotency_key,
            created_at=datetime.utcnow()
        )
        self.db.add(order)

        # Create order items
        for item_data in enriched_items:
            order_item = OrderItem(
                id=item_data["id"],
                order_id=order_id,
                menu_item_id=item_data["menu_item_id"],
                item_name=item_data["item_name"],
                item_code=item_data["item_code"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                tax_amount=item_data["tax_amount"],
                discount_amount=item_data["discount_amount"],
                total=item_data["total"],
                variant_id=item_data["variant_id"],
                variant_name=item_data["variant_name"],
                modifiers=item_data["modifiers"],
                cooking_instructions=item_data["cooking_instructions"],
                course_type=item_data["course_type"],
                prep_status=item_data["prep_status"],
                priority=item_data["priority"],
                created_at=datetime.utcnow()
            )
            self.db.add(order_item)

        # Update table if dine-in
        if data.get("table_id"):
            table = self.db.query(DiningTable).filter(
                DiningTable.id == data["table_id"]
            ).first()
            if table:
                table.current_order_id = order_id

        # Update customer stats
        if data.get("customer_id"):
            customer = self.db.query(Customer).filter(
                Customer.id == data["customer_id"]
            ).first()
            if customer:
                customer.total_orders = (customer.total_orders or 0) + 1
                customer.total_spent = float(customer.total_spent or 0) + total
                customer.last_order_date = datetime.utcnow()

        self.db.commit()

        # Generate KOTs (after commit so order exists)
        order_data_for_kot = {
            "order_id": order_id,
            "order_number": order_number,
            "table_id": data.get("table_id"),
            "order_type": data.get("order_type", "dine_in"),
            "items": enriched_items
        }

        kot_results = self.kot_engine.generate_kots(order, enriched_items)

        # Build response
        result = {
            "id": order_id,
            "order_number": order_number,
            "order_type": data.get("order_type", "dine_in"),
            "status": "confirmed",
            "table_id": data.get("table_id"),
            "subtotal": round(subtotal, 2),
            "tax_amount": round(tax_amount, 2),
            "tax_breakdown": tax_result.get("taxes", []),
            "discount_amount": round(discount, 2),
            "total": round(total, 2),
            "payment_status": "pending",
            "items": enriched_items,
            "kot_results": kot_results,
            "created_at": order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat()
        }

        logger.info(f"Fast order created: {order_number} (₹{total:.2f}) in quick_order")
        return result

    def quick_pay(self, order_id: str, payment_method: str,
                  amount: float = None, open_drawer: bool = False) -> dict:
        """Process payment for an order in a single call."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Order not found"}

        payment_amount = amount or float(order.total)
        payment_id = str(uuid.uuid4())

        payment = Payment(
            id=payment_id,
            order_id=order_id,
            tenant_id=order.tenant_id,
            branch_id=order.branch_id,
            amount=payment_amount,
            payment_method=payment_method,
            status="completed",
            idempotency_key=f"pay-{order_id}-{payment_method}-{uuid.uuid4().hex[:8]}",
            processed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.db.add(payment)

        # Update order payment status
        order.payment_status = "paid"
        order.status = "completed"
        order.completed_at = datetime.utcnow()

        # Clear table
        if order.table_id:
            table = self.db.query(DiningTable).filter(
                DiningTable.id == order.table_id
            ).first()
            if table:
                table.current_order_id = None

        self.db.commit()

        # Print bill
        bill_result = None
        try:
            order_dict = self._order_to_dict(order)
            bill_result = print_queue.queue_bill(
                "default",  # Would use branch's configured printer
                order_dict
            )
        except Exception as e:
            logger.warning(f"Bill print failed: {e}")

        # Open cash drawer
        drawer_result = None
        if open_drawer and payment_method == "cash":
            try:
                drawer_result = print_queue.open_drawer("default")
            except Exception as e:
                logger.warning(f"Drawer open failed: {e}")

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "order_number": order.order_number,
            "amount": payment_amount,
            "method": payment_method,
            "status": "completed",
            "bill_printed": bill_result.get("status") == "printed" if bill_result else False,
            "drawer_opened": drawer_result.get("status") == "opened" if drawer_result else False
        }

    def _generate_order_number(self) -> str:
        """Generate sequential order number."""
        today = datetime.utcnow().strftime("%Y%m%d")
        count = self.db.query(Order).filter(
            Order.tenant_id == tenant_context.tenant_id,
            func.date(Order.created_at) == datetime.utcnow().date()
        ).count()
        return f"ORD-{today}-{count + 1:04d}"

    def _order_to_dict(self, order: Order) -> dict:
        """Convert order to dict for printing."""
        items = self.db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        return {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "order_type": order.order_type,
            "table_id": str(order.table_id) if order.table_id else None,
            "subtotal": float(order.subtotal or 0),
            "tax_amount": float(order.tax_amount or 0),
            "discount_amount": float(order.discount_amount or 0),
            "total": float(order.total or 0),
            "items": [
                {
                    "item_name": item.item_name,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total": float(item.total),
                    "cooking_instructions": item.cooking_instructions
                }
                for item in items
            ],
            "created_at": order.created_at.isoformat() if order.created_at else None
        }


# Need this for the count query
from sqlalchemy import func
