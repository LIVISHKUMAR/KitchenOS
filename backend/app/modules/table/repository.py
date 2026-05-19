from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import DiningTable


class TableRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, table: DiningTable) -> DiningTable:
        self.db.add(table)
        self.db.commit()
        self.db.refresh(table)
        return table

    def get(self, table_id: str) -> Optional[DiningTable]:
        return self.db.query(DiningTable).filter(DiningTable.id == table_id).first()

    def get_by_number(self, branch_id: str, table_number: str) -> Optional[DiningTable]:
        return self.db.query(DiningTable).filter(
            DiningTable.branch_id == branch_id,
            DiningTable.table_number == table_number
        ).first()

    def get_all(self, branch_id: str, skip: int = 0, limit: int = 100) -> List[DiningTable]:
        return self.db.query(DiningTable).filter(
            DiningTable.branch_id == branch_id
        ).offset(skip).limit(limit).all()

    def get_available(self, branch_id: str) -> List[DiningTable]:
        return self.db.query(DiningTable).filter(
            DiningTable.branch_id == branch_id,
            DiningTable.is_active == True,
            DiningTable.current_order_id == None
        ).all()

    def update(self, table_id: str, update_data: dict) -> Optional[DiningTable]:
        db_table = self.get(table_id)
        if db_table:
            for key, value in update_data.items():
                setattr(db_table, key, value)
            self.db.commit()
            self.db.refresh(db_table)
        return db_table

    def delete(self, table_id: str) -> bool:
        db_table = self.get(table_id)
        if db_table:
            self.db.delete(db_table)
            self.db.commit()
            return True
        return False
