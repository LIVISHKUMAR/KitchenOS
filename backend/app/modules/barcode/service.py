"""Barcode and QR code service."""

import uuid
import hashlib
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import MenuItem, InventoryItem, DiningTable


class BarcodeService:
    def __init__(self, db: Session):
        self.db = db

    def lookup_by_barcode(self, barcode: str, tenant_id: str) -> dict:
        """Look up item by barcode."""
        # Check menu items
        menu_item = self.db.query(MenuItem).filter(
            MenuItem.tenant_id == tenant_id,
            MenuItem.bar_code == barcode,
            MenuItem.is_available == True
        ).first()

        if menu_item:
            return {
                "type": "menu_item",
                "id": str(menu_item.id),
                "name": menu_item.name,
                "price": float(menu_item.base_price),
                "is_veg": menu_item.is_veg
            }

        # Check inventory items
        inv_item = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.bar_code == barcode,
            InventoryItem.is_active == True
        ).first()

        if inv_item:
            return {
                "type": "inventory_item",
                "id": str(inv_item.id),
                "name": inv_item.name,
                "current_stock": float(inv_item.current_stock),
                "unit": inv_item.unit
            }

        return {"type": "not_found", "barcode": barcode}

    def generate_barcode(self, entity_type: str, entity_id: str) -> str:
        """Generate a unique barcode for an entity."""
        raw = f"{entity_type}:{entity_id}:{uuid.uuid4().hex[:8]}"
        return hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    def generate_qr_data(self, entity_type: str, entity_id: str, branch_id: str = None) -> dict:
        """Generate QR code data for different entity types."""
        if entity_type == "table":
            table = self.db.query(DiningTable).filter(DiningTable.id == entity_id).first()
            if table:
                return {
                    "type": "table",
                    "table_id": entity_id,
                    "table_number": table.table_number,
                    "branch_id": str(table.branch_id),
                    "url": f"/qr/table/{entity_id}"
                }

        elif entity_type == "menu":
            return {
                "type": "menu",
                "branch_id": branch_id,
                "url": f"/qr/menu/{branch_id or entity_id}"
            }

        elif entity_type == "order":
            return {
                "type": "order",
                "order_id": entity_id,
                "url": f"/qr/order/{entity_id}"
            }

        return {"type": entity_type, "id": entity_id}

    def assign_barcode_to_item(self, item_type: str, item_id: str, barcode: str = None) -> dict:
        """Assign or generate barcode for menu/inventory item."""
        if not barcode:
            barcode = self.generate_barcode(item_type, item_id)

        if item_type == "menu":
            item = self.db.query(MenuItem).filter(MenuItem.id == item_id).first()
            if item:
                item.bar_code = barcode
                self.db.commit()
                return {"id": item_id, "barcode": barcode, "type": "menu_item"}

        elif item_type == "inventory":
            item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
            if item:
                item.bar_code = barcode
                self.db.commit()
                return {"id": item_id, "barcode": barcode, "type": "inventory_item"}

        return {"error": "Item not found"}
