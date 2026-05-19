"""QR code generation and menu ordering service."""

import uuid
import hashlib
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import DiningTable, MenuItem, MenuCategory, Branch


class QRService:
    def __init__(self, db: Session):
        self.db = db

    def generate_table_qr(self, table_id: str, base_url: str = "https://order.kitchenos.com") -> dict:
        """Generate QR code data for a table."""
        table = self.db.query(DiningTable).filter(DiningTable.id == table_id).first()
        if not table:
            return {"error": "Table not found"}

        branch = self.db.query(Branch).filter(Branch.id == table.branch_id).first()

        qr_data = {
            "type": "table_order",
            "table_id": str(table.id),
            "table_number": table.table_number,
            "branch_id": str(table.branch_id),
            "branch_name": branch.name if branch else "",
            "url": f"{base_url}/menu?table={table_id}&branch={table.branch_id}",
        }

        # Generate QR code as SVG
        svg = self._generate_svg_qr(qr_data["url"])

        return {
            "qr_data": qr_data,
            "qr_svg": svg,
            "url": qr_data["url"]
        }

    def generate_menu_qr(self, branch_id: str, base_url: str = "https://order.kitchenos.com") -> dict:
        """Generate QR code for menu browsing."""
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            return {"error": "Branch not found"}

        url = f"{base_url}/menu?branch={branch_id}"
        svg = self._generate_svg_qr(url)

        return {
            "type": "menu",
            "branch_id": str(branch_id),
            "branch_name": branch.name,
            "url": url,
            "qr_svg": svg
        }

    def get_menu_for_table(self, table_id: str) -> dict:
        """Get menu items for a specific table's branch."""
        table = self.db.query(DiningTable).filter(DiningTable.id == table_id).first()
        if not table:
            return {"error": "Table not found"}

        categories = self.db.query(MenuCategory).filter(
            MenuCategory.branch_id == table.branch_id,
            MenuCategory.is_active == True
        ).order_by(MenuCategory.display_order).all()

        items = self.db.query(MenuItem).filter(
            MenuItem.branch_id == table.branch_id,
            MenuItem.is_available == True
        ).all()

        return {
            "table": {
                "id": str(table.id),
                "number": table.table_number,
                "capacity": table.capacity
            },
            "categories": [
                {"id": str(c.id), "name": c.name, "description": c.description}
                for c in categories
            ],
            "items": [
                {
                    "id": str(i.id),
                    "name": i.name,
                    "description": i.description,
                    "price": float(i.base_price),
                    "is_veg": i.is_veg,
                    "category_id": str(i.category_id),
                    "preparation_time": i.preparation_time_minutes
                }
                for i in items
            ]
        }

    def _generate_svg_qr(self, data: str) -> str:
        """Generate a simple SVG QR code representation.

        In production, use the 'qrcode' library:
            import qrcode
            img = qrcode.make(data)
        """
        # Simple placeholder SVG
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <rect width="200" height="200" fill="white"/>
            <text x="100" y="100" text-anchor="middle" font-size="12" fill="black">
                QR: {data[:30]}...
            </text>
        </svg>'''
