from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import DiningTable, Order
from app.modules.table.repository import TableRepository
from app.api.exceptions import BadRequestException, NotFoundException


class TableService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TableRepository(db)

    def create_table(self, data: dict) -> DiningTable:
        existing = self.repository.get_by_number(data.get("branch_id"), data.get("table_number"))
        if existing:
            raise BadRequestException(f"Table {data.get('table_number')} already exists in this branch")
        db_table = DiningTable(**data)
        return self.repository.create(db_table)

    def get_table(self, table_id: str) -> Optional[DiningTable]:
        return self.repository.get(table_id)

    def get_tables(self, branch_id: str, skip: int = 0, limit: int = 100) -> List[DiningTable]:
        return self.repository.get_all(branch_id, skip=skip, limit=limit)

    def get_available_tables(self, branch_id: str) -> List[DiningTable]:
        return self.repository.get_available(branch_id)

    def update_table(self, table_id: str, data: dict) -> Optional[DiningTable]:
        return self.repository.update(table_id, data)

    def delete_table(self, table_id: str) -> bool:
        table = self.repository.get(table_id)
        if table and table.current_order_id:
            raise BadRequestException("Cannot delete table with active order")
        return self.repository.delete(table_id)

    def transfer_table(self, from_table_id: str, to_table_id: str) -> dict:
        from_table = self.repository.get(from_table_id)
        to_table = self.repository.get(to_table_id)

        if not from_table:
            raise NotFoundException("Source table not found")
        if not to_table:
            raise NotFoundException("Target table not found")
        if not from_table.current_order_id:
            raise BadRequestException("Source table has no active order")
        if to_table.current_order_id:
            raise BadRequestException("Target table already has an active order")

        order_id = from_table.current_order_id

        # Update order's table_id
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.table_id = to_table_id

        # Update tables
        from_table.current_order_id = None
        to_table.current_order_id = order_id

        self.db.commit()

        return {
            "order_id": str(order_id),
            "from_table": from_table_id,
            "to_table": to_table_id,
            "message": f"Order transferred from table {from_table.table_number} to {to_table.table_number}"
        }

    def merge_tables(self, source_table_ids: list, target_table_id: str) -> dict:
        target_table = self.repository.get(target_table_id)
        if not target_table:
            raise NotFoundException("Target table not found")

        merged_orders = []
        for source_id in source_table_ids:
            source_table = self.repository.get(source_id)
            if source_table and source_table.current_order_id:
                order = self.db.query(Order).filter(Order.id == source_table.current_order_id).first()
                if order:
                    order.table_id = target_table_id
                    merged_orders.append(str(order.id))
                source_table.current_order_id = None

        if merged_orders:
            target_table.current_order_id = merged_orders[-1]  # Set to latest order

        self.db.commit()

        return {
            "merged_orders": merged_orders,
            "target_table": target_table_id,
            "message": f"{len(merged_orders)} order(s) merged to table {target_table.table_number}"
        }
