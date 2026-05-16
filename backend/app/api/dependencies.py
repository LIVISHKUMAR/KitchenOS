from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.database import get_db_session
from app.core.security import decode_token
from app.core.config import tenant_context

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    tenant_context.set(
        tenant_id=payload.get("tenant_id"),
        branch_id=payload.get("branch_id"),
        user_id=payload.get("user_id")
    )

    return {
        "user_id": payload.get("user_id"),
        "tenant_id": payload.get("tenant_id"),
        "branch_id": payload.get("branch_id"),
        "role": payload.get("role")
    }


def require_role(*roles):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def get_tenant_id(current_user: dict = Depends(get_current_user)) -> str:
    return current_user.get("tenant_id")


def get_branch_id(current_user: dict = Depends(get_current_user)) -> Optional[str]:
    return current_user.get("branch_id")
