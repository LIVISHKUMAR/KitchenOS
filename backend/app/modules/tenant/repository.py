from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Tenant


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def get(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        return self.db.query(Tenant).offset(skip).limit(limit).all()

    def update(self, tenant_id: str, update_data: dict) -> Optional[Tenant]:
        db_tenant = self.get(tenant_id)
        if db_tenant:
            for field, value in update_data.items():
                setattr(db_tenant, field, value)
            self.db.commit()
            self.db.refresh(db_tenant)
        return db_tenant

    def delete(self, tenant_id: str) -> bool:
        db_tenant = self.get(tenant_id)
        if db_tenant:
            self.db.delete(db_tenant)
            self.db.commit()
            return True
        return False
