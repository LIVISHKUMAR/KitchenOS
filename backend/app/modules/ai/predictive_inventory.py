"""Predictive Inventory System.

Predicts inventory needs based on:
- Demand forecast
- Historical consumption patterns
- Lead times from vendors
- Waste patterns
- Seasonal trends
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import InventoryItem, StockMovement, PurchaseOrder, Vendor, MenuItem

logger = logging.getLogger("kitchenos.ai.predictive_inventory")


class PredictiveInventoryEngine:
    """AI-powered inventory prediction and auto-reorder."""

    def __init__(self, db: Session):
        self.db = db

    def predict_consumption(self, tenant_id: str, branch_id: str,
                            days_ahead: int = 7) -> Dict:
        """Predict inventory consumption for the next N days."""
        # Get historical consumption
        consumption = self._get_historical_consumption(tenant_id, branch_id)

        # Get current stock
        current_stock = self._get_current_stock(tenant_id, branch_id)

        # Predict needs
        predictions = []
        for item_id, data in consumption.items():
            daily_avg = data["daily_avg"]
            current = current_stock.get(item_id, {}).get("stock", 0)
            unit = current_stock.get(item_id, {}).get("unit", "pcs")

            predicted_consumption = daily_avg * days_ahead
            days_until_stockout = current / daily_avg if daily_avg > 0 else 999

            needs_reorder = days_until_stockout < 3  # Less than 3 days of stock
            order_quantity = max(0, predicted_consumption * 1.2 - current)  # 20% buffer

            predictions.append({
                "item_id": item_id,
                "item_name": data["name"],
                "unit": unit,
                "current_stock": round(current, 2),
                "daily_avg_consumption": round(daily_avg, 2),
                "predicted_consumption_7d": round(predicted_consumption, 2),
                "days_until_stockout": round(days_until_stockout, 1),
                "needs_reorder": needs_reorder,
                "suggested_order_quantity": round(order_quantity, 2),
                "preferred_vendor": data.get("vendor_name"),
                "lead_time_days": data.get("lead_time", 3)
            })

        # Sort by urgency
        predictions.sort(key=lambda x: x["days_until_stockout"])

        # Generate purchase suggestions
        reorder_items = [p for p in predictions if p["needs_reorder"]]

        return {
            "branch_id": branch_id,
            "predictions": predictions,
            "reorder_alerts": reorder_items,
            "total_items_tracked": len(predictions),
            "items_needing_reorder": len(reorder_items),
            "estimated_reorder_cost": sum(
                p["suggested_order_quantity"] * 100  # Placeholder cost
                for p in reorder_items
            )
        }

    def _get_historical_consumption(self, tenant_id: str,
                                      branch_id: str) -> Dict:
        """Get historical consumption patterns."""
        days_back = 30
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        movements = self.db.query(
            StockMovement.inventory_item_id,
            func.sum(StockMovement.quantity).label('total_consumed')
        ).filter(
            StockMovement.movement_type.in_(["sale", "waste"]),
            StockMovement.created_at >= cutoff
        ).group_by(
            StockMovement.inventory_item_id
        ).all()

        result = {}
        for m in movements:
            item = self.db.query(InventoryItem).filter(
                InventoryItem.id == m.inventory_item_id
            ).first()

            if item and item.tenant_id == tenant_id:
                result[str(m.inventory_item_id)] = {
                    "name": item.name,
                    "daily_avg": float(m.total_consumed) / days_back,
                    "vendor_name": None,
                    "lead_time": 3
                }

        return result

    def _get_current_stock(self, tenant_id: str,
                            branch_id: str) -> Dict:
        """Get current stock levels."""
        items = self.db.query(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.is_active == True
        )

        if branch_id:
            items = items.filter(InventoryItem.branch_id == branch_id)

        items = items.all()

        return {
            str(item.id): {
                "stock": float(item.current_stock),
                "unit": item.unit,
                "min_stock": float(item.minimum_stock or 0)
            }
            for item in items
        }

    def generate_purchase_orders(self, tenant_id: str,
                                  branch_id: str) -> List[Dict]:
        """Auto-generate purchase order suggestions."""
        prediction = self.predict_consumption(tenant_id, branch_id)
        reorder_items = prediction["reorder_alerts"]

        if not reorder_items:
            return []

        # Group by vendor
        vendor_items = {}
        for item in reorder_items:
            vendor = item.get("preferred_vendor") or "default"
            if vendor not in vendor_items:
                vendor_items[vendor] = []
            vendor_items[vendor].append(item)

        # Generate PO suggestions
        po_suggestions = []
        for vendor, items in vendor_items.items():
            total_cost = sum(i["suggested_order_quantity"] * 100 for i in items)

            po_suggestions.append({
                "vendor": vendor,
                "items": [
                    {
                        "item_name": i["item_name"],
                        "quantity": i["suggested_order_quantity"],
                        "unit": i["unit"],
                        "estimated_cost": i["suggested_order_quantity"] * 100
                    }
                    for i in items
                ],
                "total_items": len(items),
                "estimated_total": total_cost,
                "urgency": "high" if any(i["days_until_stockout"] < 1 for i in items) else "normal"
            })

        return po_suggestions

    def analyze_waste(self, tenant_id: str, branch_id: str,
                      days_back: int = 30) -> Dict:
        """Analyze waste patterns to improve predictions."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        waste = self.db.query(
            StockMovement.inventory_item_id,
            func.sum(StockMovement.quantity).label('total_waste'),
            func.count(StockMovement.id).label('waste_count')
        ).join(InventoryItem).filter(
            InventoryItem.tenant_id == tenant_id,
            StockMovement.movement_type == "waste",
            StockMovement.created_at >= cutoff
        ).group_by(
            StockMovement.inventory_item_id
        ).all()

        total_waste = sum(float(w.total_waste) for w in waste)

        items = []
        for w in waste:
            item = self.db.query(InventoryItem).filter(
                InventoryItem.id == w.inventory_item_id
            ).first()
            if item:
                items.append({
                    "item_name": item.name,
                    "waste_quantity": float(w.total_waste),
                    "waste_count": w.waste_count,
                    "unit": item.unit,
                    "waste_percentage": 0  # Would calculate against total consumed
                })

        return {
            "period_days": days_back,
            "total_waste": round(total_waste, 2),
            "items": sorted(items, key=lambda x: x["waste_quantity"], reverse=True),
            "recommendation": "Review expiry dates and ordering quantities for high-waste items."
        }
