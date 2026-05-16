from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Tenant
from app.modules.tenant.schemas import TenantCreate, TenantUpdate

class TenantService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        db_tenant = Tenant(**tenant_data.dict())
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        return db_tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()
    
    def get_tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        return self.db.query(Tenant).offset(skip).limit(limit).all()
    
    def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Optional[Tenant]:
        db_tenant = self.get_tenant(tenant_id)
        if db_tenant:
            for field, value in tenant_data.dict(exclude_unset=True).items():
                setattr(db_tenant, field, value)
            self.db.commit()
            self.db.refresh(db_tenant)
        return db_tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        db_tenant = self.get_tenant(tenant_id)
        if db_tenant:
            self.db.delete(db_tenant)
            self.db.commit()
            return True
        return False
