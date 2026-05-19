from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Customer
from app.modules.customer.repository import CustomerRepository


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomerRepository(db)

    def create_customer(self, customer_data: dict) -> Customer:
        db_customer = Customer(**customer_data)
        return self.repository.create(db_customer)

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.repository.get(customer_id)

    def get_customer_by_phone(self, phone: str, tenant_id: str) -> Optional[Customer]:
        return self.repository.get_by_phone(phone, tenant_id)

    def get_customers(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.repository.get_all(tenant_id=tenant_id, skip=skip, limit=limit)

    def update_customer(self, customer_id: str, customer_data: dict) -> Optional[Customer]:
        return self.repository.update(customer_id, customer_data)

    def delete_customer(self, customer_id: str) -> bool:
        return self.repository.delete(customer_id)
