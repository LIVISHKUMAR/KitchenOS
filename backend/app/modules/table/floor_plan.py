"""Visual floor plan management."""

import uuid
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, JSON, DateTime, Integer, Boolean
from app.infrastructure.database import Base
from app.models import generate_uuid, DiningTable, Order


class FloorPlan(Base):
    __tablename__ = "floor_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    layout = Column(JSON, nullable=False)  # {tables: [{id, x, y, width, height, shape}]}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class FloorPlanService:
    def __init__(self, db: Session):
        self.db = db

    def create_floor_plan(self, tenant_id: str, branch_id: str,
                          name: str, tables: List[dict]) -> FloorPlan:
        """Create a floor plan with table positions."""
        layout = {"tables": tables}

        plan = FloorPlan(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            name=name,
            layout=layout
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_floor_plan(self, branch_id: str) -> Optional[dict]:
        """Get floor plan with live table status."""
        plan = self.db.query(FloorPlan).filter(
            FloorPlan.branch_id == branch_id,
            FloorPlan.is_active == True
        ).first()

        if not plan:
            return self._generate_default_plan(branch_id)

        # Enrich with live status
        tables_with_status = []
        for table_def in plan.layout.get("tables", []):
            table = self.db.query(DiningTable).filter(
                DiningTable.id == table_def.get("id")
            ).first()

            status = "available"
            order_info = None

            if table:
                if table.current_order_id:
                    status = "occupied"
                    order = self.db.query(Order).filter(
                        Order.id == table.current_order_id
                    ).first()
                    if order:
                        order_info = {
                            "order_id": str(order.id),
                            "order_number": order.order_number,
                            "status": order.status,
                            "total": float(order.total),
                            "created_at": order.created_at.isoformat() if order.created_at else None
                        }

            tables_with_status.append({
                **table_def,
                "status": status,
                "order": order_info,
                "table_number": table.table_number if table else table_def.get("number"),
                "capacity": table.capacity if table else table_def.get("capacity", 4)
            })

        return {
            "id": str(plan.id),
            "name": plan.name,
            "tables": tables_with_status
        }

    def update_table_position(self, plan_id: str, table_id: str,
                               x: int, y: int) -> bool:
        """Update a table's position in the floor plan."""
        plan = self.db.query(FloorPlan).filter(FloorPlan.id == plan_id).first()
        if not plan:
            return False

        tables = plan.layout.get("tables", [])
        for t in tables:
            if t.get("id") == table_id:
                t["x"] = x
                t["y"] = y
                break

        plan.layout = {"tables": tables}
        self.db.commit()
        return True

    def add_table_to_plan(self, plan_id: str, table_data: dict) -> bool:
        """Add a table to the floor plan."""
        plan = self.db.query(FloorPlan).filter(FloorPlan.id == plan_id).first()
        if not plan:
            return False

        tables = plan.layout.get("tables", [])
        tables.append(table_data)
        plan.layout = {"tables": tables}
        self.db.commit()
        return True

    def _generate_default_plan(self, branch_id: str) -> dict:
        """Generate a default floor plan from existing tables."""
        tables = self.db.query(DiningTable).filter(
            DiningTable.branch_id == branch_id,
            DiningTable.is_active == True
        ).all()

        layout_tables = []
        x, y = 50, 50
        for i, table in enumerate(tables):
            status = "occupied" if table.current_order_id else "available"
            layout_tables.append({
                "id": str(table.id),
                "number": table.table_number,
                "capacity": table.capacity,
                "section": table.section,
                "x": x,
                "y": y,
                "width": 80,
                "height": 80,
                "shape": "square",
                "status": status
            })
            x += 100
            if (i + 1) % 5 == 0:
                x = 50
                y += 100

        return {
            "id": None,
            "name": "Default Layout",
            "tables": layout_tables
        }

    def get_sections(self, branch_id: str) -> List[str]:
        """Get unique sections for a branch."""
        tables = self.db.query(DiningTable.section).filter(
            DiningTable.branch_id == branch_id,
            DiningTable.is_active == True,
            DiningTable.section.isnot(None)
        ).distinct().all()

        return [t.section for t in tables if t.section]
