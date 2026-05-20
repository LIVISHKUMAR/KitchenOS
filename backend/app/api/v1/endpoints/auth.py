from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
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


# --- Session Management ---

from app.api.dependencies import get_current_user
from app.models import User
import redis

# In-memory session store (use Redis in production)
_active_sessions: dict = {}


@router.post("/sessions/track")
async def track_session(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Track active session for the current user."""
    import uuid
    session_id = str(uuid.uuid4())
    user_id = current_user["user_id"]
    if user_id not in _active_sessions:
        _active_sessions[user_id] = []
    _active_sessions[user_id].append({
        "session_id": session_id,
        "user_id": user_id,
        "tenant_id": current_user["tenant_id"],
        "role": current_user["role"],
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
    })
    # Limit to 3 concurrent sessions
    if len(_active_sessions[user_id]) > 3:
        _active_sessions[user_id] = _active_sessions[user_id][-3:]
    return {"session_id": session_id, "active_sessions": len(_active_sessions[user_id])}


@router.get("/sessions")
async def list_sessions(
    current_user: dict = Depends(get_current_user)
):
    """List active sessions for the current user."""
    user_id = current_user["user_id"]
    return _active_sessions.get(user_id, [])


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a specific session."""
    user_id = current_user["user_id"]
    sessions = _active_sessions.get(user_id, [])
    _active_sessions[user_id] = [s for s in sessions if s["session_id"] != session_id]
    return {"message": "Session revoked", "remaining": len(_active_sessions[user_id])}


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: dict = Depends(get_current_user)
):
    """Revoke all sessions for the current user (force logout all devices)."""
    user_id = current_user["user_id"]
    count = len(_active_sessions.get(user_id, []))
    _active_sessions[user_id] = []
    return {"message": f"All {count} sessions revoked"}


@router.get("/sessions/all")
async def list_all_sessions(
    current_user: dict = Depends(get_current_user)
):
    """List all active sessions (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    all_sessions = []
    for user_id, sessions in _active_sessions.items():
        all_sessions.extend(sessions)
    return all_sessions
