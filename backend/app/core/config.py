from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "RestroPOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL")
    CACHE_TTL: int = 300  # 5 minutes
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL")
    
    # Tenant Settings
    MAX_TENANTS_FREE: int = 1
    MAX_BRANCHES_FREE: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Multi-tenant context
class TenantContext:
    tenant_id: str = None
    branch_id: str = None
    user_id: str = None
    
    def set(self, tenant_id: str = None, branch_id: str = None, user_id: str = None):
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.user_id = user_id
    
    def clear(self):
        self.tenant_id = None
        self.branch_id = None
        self.user_id = None

tenant_context = TenantContext()