from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Tenant
from app.modules.tenant.repository import TenantRepository


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantRepository(db)

    def create_tenant(self, tenant_data) -> Tenant:
        if hasattr(tenant_data, 'model_dump'):
            data = tenant_data.model_dump()
        elif hasattr(tenant_data, 'dict'):
            data = tenant_data.dict()
        else:
            data = tenant_data
        db_tenant = Tenant(**data)
        return self.repository.create(db_tenant)

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.repository.get(tenant_id)

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        return self.repository.get_by_slug(slug)

    def get_tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        return self.repository.get_all(skip=skip, limit=limit)

    def update_tenant(self, tenant_id: str, tenant_data) -> Optional[Tenant]:
        if hasattr(tenant_data, 'model_dump'):
            data = tenant_data.model_dump(exclude_unset=True)
        elif hasattr(tenant_data, 'dict'):
            data = tenant_data.dict(exclude_unset=True)
        else:
            data = tenant_data
        return self.repository.update(tenant_id, data)

    def delete_tenant(self, tenant_id: str) -> bool:
        return self.repository.delete(tenant_id)
