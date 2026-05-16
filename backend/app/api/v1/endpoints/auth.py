from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db_session
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import tenant_context
from app.models import User

router = APIRouter()

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set tenant context
    tenant_context.set(
        tenant_id=str(user.tenant_id),
        branch_id=str(user.branch_id) if user.branch_id else None,
        user_id=str(user.id)
    )
    
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "role": user.role
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id)
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db_session)
):
    # In a real implementation, you would validate the refresh token
    # For now, we'll just return a new access token
    # This is a simplified version
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not fully implemented"
    )

@router.post("/logout")
async def logout():
    # Clear tenant context
    tenant_context.clear()
    return {"message": "Successfully logged out"}