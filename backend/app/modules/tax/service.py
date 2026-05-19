from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import TaxConfig


class TaxService:
    def __init__(self, db: Session):
        self.db = db

    def create_tax_config(self, data: dict) -> TaxConfig:
        db_tax = TaxConfig(**data)
        self.db.add(db_tax)
        self.db.commit()
        self.db.refresh(db_tax)
        return db_tax

    def get_tax_config(self, tax_id: str) -> Optional[TaxConfig]:
        return self.db.query(TaxConfig).filter(TaxConfig.id == tax_id).first()

    def get_tax_configs(self, tenant_id: str, branch_id: Optional[str] = None) -> List[TaxConfig]:
        query = self.db.query(TaxConfig).filter(
            TaxConfig.tenant_id == tenant_id,
            TaxConfig.is_active == True
        )
        if branch_id:
            query = query.filter(
                (TaxConfig.branch_id == branch_id) | (TaxConfig.branch_id == None)
            )
        return query.all()

    def calculate_tax(self, tenant_id: str, subtotal: float, order_type: str = "dine_in",
                      branch_id: Optional[str] = None) -> dict:
        tax_configs = self.get_tax_configs(tenant_id, branch_id)

        applicable_taxes = []
        total_tax = 0.0

        for tax in tax_configs:
            applicable_to = tax.applicable_to or ["dine_in", "takeaway", "delivery"]
            if order_type in applicable_to:
                tax_amount = subtotal * (float(tax.rate) / 100)
                applicable_taxes.append({
                    "tax_id": str(tax.id),
                    "name": tax.name,
                    "rate": float(tax.rate),
                    "type": tax.tax_type,
                    "amount": round(tax_amount, 2)
                })
                total_tax += tax_amount

        return {
            "subtotal": subtotal,
            "taxes": applicable_taxes,
            "total_tax": round(total_tax, 2),
            "total": round(subtotal + total_tax, 2)
        }

    def update_tax_config(self, tax_id: str, data: dict) -> Optional[TaxConfig]:
        db_tax = self.get_tax_config(tax_id)
        if db_tax:
            for key, value in data.items():
                setattr(db_tax, key, value)
            self.db.commit()
            self.db.refresh(db_tax)
        return db_tax

    def delete_tax_config(self, tax_id: str) -> bool:
        db_tax = self.get_tax_config(tax_id)
        if db_tax:
            db_tax.is_active = False
            self.db.commit()
            return True
        return False
