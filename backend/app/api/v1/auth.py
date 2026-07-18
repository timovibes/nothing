#the actual HTTP routes — /register, /login, /refresh, /logout, and /me
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.identity import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.api.deps import get_current_user
from app.models.identity import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db)
    client_ip = request.client.host if request.client else None
    device = request.headers.get("user-agent")
    return service.login(payload, ip_address=client_ip, device=device)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.logout(payload.refresh_token)
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.repositories.audit_repository import AuditRepository
    AuditRepository(db).create_activity_log(user_id=current_user.id, activity_type="viewed_profile")
    return current_user
