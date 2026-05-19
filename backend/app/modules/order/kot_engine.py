"""KOT Auto-Generation Engine.

Automatically generates Kitchen Order Tickets when orders are created.
Routes items to different printers based on category.
Manages course sequencing.
"""

import uuid
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, MenuItem, MenuCategory
from app.modules.printer.escpos import print_queue

logger = logging.getLogger("kitchenos.kot")


class KOTEngine:
    """Automatic KOT generation and printer routing."""

    def __init__(self, db: Session):
        self.db = db

    def generate_kots(self, order: Order, items: List[dict],
                      printer_config: dict = None) -> List[dict]:
        """Generate KOTs for an order, routing items to appropriate printers.

        Args:
            order: The order object
            items: List of order items with menu_item_id, quantity, etc.
            printer_config: Dict mapping category_id → printer_id

        Returns:
            List of KOT results
        """
        if not printer_config:
            # Default: all items to default printer
            printer_config = {"default": "default"}

        # Group items by printer
        printer_items: Dict[str, List[dict]] = {}

        for item_data in items:
            menu_item_id = item_data.get("menu_item_id")
            menu_item = self.db.query(MenuItem).filter(
                MenuItem.id == menu_item_id
            ).first()

            # Determine which printer to use
            printer_id = "default"
            if menu_item and menu_item.printer_routing:
                # Check item-level printer routing
                printer_id = menu_item.printer_routing.get("printer_id", "default")
            elif menu_item and menu_item.category_id:
                # Check category-level printer routing
                category = self.db.query(MenuCategory).filter(
                    MenuCategory.id == menu_item.category_id
                ).first()
                if category and hasattr(category, 'printer_routing') and category.printer_routing:
                    printer_id = category.printer_routing.get("printer_id", "default")

            # Check config override
            if menu_item and str(menu_item.category_id) in printer_config:
                printer_id = printer_config[str(menu_item.category_id)]

            if printer_id not in printer_items:
                printer_items[printer_id] = []

            printer_items[printer_id].append({
                "item_name": item_data.get("item_name", menu_item.name if menu_item else "Unknown"),
                "quantity": item_data.get("quantity", 1),
                "cooking_instructions": item_data.get("cooking_instructions"),
                "course_type": item_data.get("course_type", "main"),
                "variant_name": item_data.get("variant_name"),
                "modifiers": item_data.get("modifiers", [])
            })

        # Generate KOT for each printer
        results = []
        order_data = {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "table_id": str(order.table_id) if order.table_id else "Takeaway",
            "order_type": order.order_type or "dine_in",
            "created_at": order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat()
        }

        # Sort items by course: starters → mains → desserts
        course_order = {"starter": 0, "appetizer": 0, "main": 1, "dessert": 2, "beverage": 3}

        for printer_id, items_for_printer in printer_items.items():
            # Sort by course
            sorted_items = sorted(
                items_for_printer,
                key=lambda x: course_order.get(x.get("course_type", "main"), 1)
            )

            kot_data = {
                **order_data,
                "items": sorted_items,
                "kot_number": f"KOT-{order.order_number}-{printer_id}"
            }

            result = print_queue.queue_kot(printer_id, kot_data)
            results.append(result)

            if result.get("status") == "printed":
                logger.info(f"KOT printed: {kot_data['kot_number']} on printer {printer_id}")
            else:
                logger.warning(f"KOT print failed: {kot_data['kot_number']} on printer {printer_id}")

        return results

    def check_all_items_ready(self, order_id: str) -> bool:
        """Check if all items in an order are ready."""
        items = self.db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()

        return all(
            item.prep_status in ("ready", "served")
            for item in items
        )

    def get_kot_summary(self, order_id: str) -> dict:
        """Get KOT summary for an order."""
        items = self.db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()

        summary = {
            "total_items": len(items),
            "pending": 0,
            "preparing": 0,
            "ready": 0,
            "served": 0
        }

        for item in items:
            status = item.prep_status or "pending"
            if status in summary:
                summary[status] += 1

        summary["all_ready"] = summary["ready"] + summary["served"] == summary["total_items"]

        return summary
