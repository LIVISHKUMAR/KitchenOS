from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_phone(self, phone: str, tenant_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(
            Customer.phone == phone,
            Customer.tenant_id == tenant_id
        ).first()

    def get_all(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.db.query(Customer).filter(Customer.tenant_id == tenant_id).offset(skip).limit(limit).all()

    def update(self, customer_id: str, update_data: dict) -> Optional[Customer]:
        db_customer = self.get(customer_id)
        if db_customer:
            for field, value in update_data.items():
                setattr(db_customer, field, value)
            self.db.commit()
            self.db.refresh(db_customer)
        return db_customer

    def delete(self, customer_id: str) -> bool:
        db_customer = self.get(customer_id)
        if db_customer:
            self.db.delete(db_customer)
            self.db.commit()
            return True
        return False
