from pydantic_settings import BaseSettings
from typing import Optional
from contextvars import ContextVar


class Settings(BaseSettings):
    # App
    APP_NAME: str = "KitchenOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./kitchenos.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # Recycle connections every 30 minutes
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes

    # RabbitMQ
    RABBITMQ_URL: Optional[str] = "amqp://guest:guest@localhost:5672/"

    # Tenant Settings
    MAX_TENANTS_FREE: int = 1
    MAX_BRANCHES_FREE: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context) -> None:
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set. Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )


settings = Settings()

# Thread-safe multi-tenant context using contextvars
_tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
_branch_id_var: ContextVar[Optional[str]] = ContextVar("branch_id", default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class TenantContext:
    """Thread-safe tenant context using Python contextvars.

    Each async request gets its own isolated copy of these variables,
    preventing cross-tenant data corruption under concurrent requests.
    """

    @property
    def tenant_id(self) -> Optional[str]:
        return _tenant_id_var.get()

    @property
    def branch_id(self) -> Optional[str]:
        return _branch_id_var.get()

    @property
    def user_id(self) -> Optional[str]:
        return _user_id_var.get()

    def set(self, tenant_id: Optional[str] = None, branch_id: Optional[str] = None, user_id: Optional[str] = None):
        _tenant_id_var.set(tenant_id)
        _branch_id_var.set(branch_id)
        _user_id_var.set(user_id)

    def clear(self):
        _tenant_id_var.set(None)
        _branch_id_var.set(None)
        _user_id_var.set(None)


tenant_context = TenantContext()
