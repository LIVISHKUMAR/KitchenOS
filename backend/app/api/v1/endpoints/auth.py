from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db_session
from app.core.config import tenant_context
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RegisterResponse

router = APIRouter()


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    auth_service = AuthService(db)
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    result = auth_service.login(login_data)
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": "bearer"
    }


@router.post("/register", response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db_session)
):
    auth_service = AuthService(db)
    return auth_service.register(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    body: RefreshRequest,
    db: Session = Depends(get_db_session)
):
    auth_service = AuthService(db)
    result = auth_service.refresh_access_token(body.refresh_token)
    return {
        "access_token": result["access_token"],
        "refresh_token": body.refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout():
    tenant_context.clear()
    return {"message": "Successfully logged out"}
