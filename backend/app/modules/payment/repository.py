from typing import Optional
from sqlalchemy.orm import Session
from app.models import Payment


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get(self, payment_id: str) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_by_order(self, order_id: str) -> list:
        return self.db.query(Payment).filter(Payment.order_id == order_id).all()

    def update(self, payment_id: str, update_data: dict) -> Optional[Payment]:
        db_payment = self.get(payment_id)
        if db_payment:
            for key, value in update_data.items():
                setattr(db_payment, key, value)
            self.db.commit()
            self.db.refresh(db_payment)
        return db_payment

    def get_all(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list:
        return self.db.query(Payment).filter(Payment.tenant_id == tenant_id).offset(skip).limit(limit).all()
