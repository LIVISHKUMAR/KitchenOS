from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Customer
from app.modules.customer.schemas import CustomerCreate, CustomerUpdate

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        db_customer = Customer(**customer_data.dict())
        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_customer_by_phone(self, phone: str, tenant_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(
            and_(Customer.phone == phone, Customer.tenant_id == tenant_id)
        ).first()
    
    def get_customers(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.db.query(Customer).filter(Customer.tenant_id == tenant_id).offset(skip).limit(limit).all()
    
    def update_customer(self, customer_id: str, customer_data: CustomerUpdate) -> Optional[Customer]:
        db_customer = self.get_customer(customer_id)
        if db_customer:
            for field, value in customer_data.dict(exclude_unset=True).items():
                setattr(db_customer, field, value)
            self.db.commit()
            self.db.refresh(db_customer)
        return db_customer
    
    def delete_customer(self, customer_id: str) -> bool:
        db_customer = self.get_customer(customer_id)
        if db_customer:
            self.db.delete(db_customer)
            self.db.commit()
            return True
        return False
