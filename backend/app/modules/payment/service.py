from typing import Optional
from sqlalchemy.orm import Session
from app.models import Payment
import uuid
from datetime import datetime

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_payment(self, payment_data: dict) -> Payment:
        db_payment = Payment(**payment_data)
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return db_payment
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_payments_by_order(self, order_id: str) -> list:
        return self.db.query(Payment).filter(Payment.order_id == order_id).all()
    
    def update_payment(self, payment_id: str, payment_data: dict) -> Optional[Payment]:
        db_payment = self.get_payment(payment_id)
        if db_payment:
            for key, value in payment_data.items():
                setattr(db_payment, key, value)
            self.db.commit()
            self.db.refresh(db_payment)
        return db_payment
    
    def get_payments(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list:
        return self.db.query(Payment).filter(Payment.tenant_id == tenant_id).offset(skip).limit(limit).all()
