from typing import Optional
from sqlalchemy.orm import Session
from app.models import Payment
from app.modules.payment.repository import PaymentRepository


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PaymentRepository(db)

    def create_payment(self, payment_data: dict) -> Payment:
        db_payment = Payment(**payment_data)
        return self.repository.create(db_payment)

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self.repository.get(payment_id)

    def get_payments_by_order(self, order_id: str) -> list:
        return self.repository.get_by_order(order_id)

    def update_payment(self, payment_id: str, payment_data: dict) -> Optional[Payment]:
        return self.repository.update(payment_id, payment_data)

    def get_payments(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list:
        return self.repository.get_all(tenant_id=tenant_id, skip=skip, limit=limit)
