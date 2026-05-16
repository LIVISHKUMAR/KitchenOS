import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.modules.auth.schemas import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import tenant_context
from app.api.exceptions import UnauthorizedException, BadRequestException, ConflictException
from app.models import Tenant, User, Branch


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterRequest) -> dict:
        existing_tenant = self.db.query(Tenant).filter(
            and_(Tenant.email == data.email)
        ).first()

        if existing_tenant:
            raise ConflictException("Email already registered")

        tenant_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        tenant = Tenant(
            id=tenant_id,
            name=data.name,
            slug=data.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8],
            email=data.email,
            phone=data.phone,
            business_type=data.business_type,
            subscription_plan="trial",
            subscription_status="trial",
            max_branches=1,
            max_users=5,
            max_terminals=2,
            is_active=True
        )

        branch = Branch(
            id=branch_id,
            tenant_id=tenant_id,
            name=f"{data.name} - Main",
            code="MAIN",
            is_active=True
        )

        password_hash = hash_password(data.password)
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            email=data.email,
            password_hash=password_hash,
            first_name=data.name,
            phone=data.phone,
            role="admin",
            is_active=True
        )

        self.db.add(tenant)
        self.db.add(branch)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(tenant)
        self.db.refresh(branch)
        self.db.refresh(user)

        access_token = create_access_token({
            "user_id": user_id,
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "role": "admin"
        })

        refresh_token = create_refresh_token({
            "user_id": user_id,
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "role": "admin"
        })

        return {
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "email": tenant.email,
                "subscription_plan": tenant.subscription_plan
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "role": user.role
            },
            "branch_id": branch_id,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def login(self, data: LoginRequest) -> dict:
        user = self.db.query(User).filter(
            and_(User.email == data.email, User.is_active == True)
        ).first()

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        self.db.query(User).filter(User.id == user.id).update({
            "last_login_at": datetime.utcnow()
        })
        self.db.commit()

        access_token = create_access_token({
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "role": user.role
        })

        refresh_token = create_refresh_token({
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "role": user.role
        })

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "role": user.role,
                "tenant_id": str(user.tenant_id)
            },
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("user_id")
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.is_active == True)
        ).first()

        if not user:
            raise UnauthorizedException("User not found")

        access_token = create_access_token({
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "role": user.role
        })

        return {
            "access_token": access_token
        }
