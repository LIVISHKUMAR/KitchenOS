"""Advanced inventory features: multi-unit, waste tracking, batch tracking."""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import InventoryItem, StockMovement


class AdvancedInventoryService:
    def __init__(self, db: Session):
        self.db = db

    # Unit conversion rates (base unit -> target unit)
    UNIT_CONVERSIONS = {
        "kg": {"g": 1000, "mg": 1000000},
        "g": {"kg": 0.001, "mg": 1000},
        "l": {"ml": 1000, "cl": 100},
        "ml": {"l": 0.001},
        "pcs": {"dz": 0.0833},
        "dz": {"pcs": 12}
    }

    def convert_unit(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """Convert quantity between units."""
        if from_unit == to_unit:
            return quantity
        conversions = self.UNIT_CONVERSIONS.get(from_unit, {})
        rate = conversions.get(to_unit)
        if rate:
            return quantity * rate
        return quantity

    def log_waste(self, inventory_item_id: str, quantity: float, reason: str,
                  branch_id: str, user_id: str) -> StockMovement:
        """Log inventory waste."""
        movement = StockMovement(
            id=str(uuid.uuid4()),
            inventory_item_id=inventory_item_id,
            branch_id=branch_id,
            movement_type="waste",
            quantity=quantity,
            reference_type="waste_log",
            notes=reason,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(movement)

        # Update stock
        item = self.db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
        if item:
            item.current_stock = float(item.current_stock) - quantity

        self.db.commit()
        return movement

    def get_waste_report(self, tenant_id: str, branch_id: Optional[str] = None,
                         date_from: Optional[str] = None, date_to: Optional[str] = None) -> dict:
        """Generate waste report."""
        query = self.db.query(StockMovement).join(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            StockMovement.movement_type == "waste"
        )
        if branch_id:
            query = query.filter(StockMovement.branch_id == branch_id)

        movements = query.all()

        total_waste = sum(float(m.quantity) for m in movements)
        waste_by_reason = {}
        for m in movements:
            reason = m.notes or "Unknown"
            waste_by_reason[reason] = waste_by_reason.get(reason, 0) + float(m.quantity)

        return {
            "total_waste_quantity": total_waste,
            "waste_entries": len(movements),
            "waste_by_reason": waste_by_reason
        }

    def get_stock_valuation(self, tenant_id: str, branch_id: Optional[str] = None,
                            method: str = "weighted_avg") -> dict:
        """Calculate stock valuation."""
        query = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_active == True
        )
        if branch_id:
            query = query.filter(InventoryItem.branch_id == branch_id)

        items = query.all()

        total_value = 0.0
        item_values = []

        for item in items:
            stock = float(item.current_stock)
            cost = float(item.cost_price or 0)
            value = stock * cost
            total_value += value
            item_values.append({
                "id": str(item.id),
                "name": item.name,
                "stock": stock,
                "unit": item.unit,
                "cost_price": cost,
                "value": round(value, 2)
            })

        return {
            "method": method,
            "total_value": round(total_value, 2),
            "item_count": len(items),
            "items": sorted(item_values, key=lambda x: x["value"], reverse=True)
        }

    def get_batch_info(self, inventory_item_id: str) -> list:
        """Get batch information for an item."""
        movements = self.db.query(StockMovement).filter(
            StockMovement.inventory_item_id == inventory_item_id,
            StockMovement.batch_number.isnot(None)
        ).order_by(StockMovement.created_at.asc()).all()

        batches = {}
        for m in movements:
            batch = m.batch_number
            if batch not in batches:
                batches[batch] = {
                    "batch_number": batch,
                    "quantity": 0,
                    "expiry_date": m.expiry_date.isoformat() if m.expiry_date else None,
                    "movements": []
                }
            if m.movement_type in ("purchase", "return"):
                batches[batch]["quantity"] += float(m.quantity)
            else:
                batches[batch]["quantity"] -= float(m.quantity)
            batches[batch]["movements"].append({
                "type": m.movement_type,
                "quantity": float(m.quantity),
                "date": m.created_at.isoformat() if m.created_at else None
            })

        return list(batches.values())
