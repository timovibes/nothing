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
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.api.deps import get_current_user
from app.models.identity import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.identity import ChangePasswordRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(payload)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.verify_email(payload.email, payload.code)
    return None


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.resend_verification_email(payload.email)
    return None


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
    AuditRepository(db).create_activity_log(user_id=current_user.id, activity_type="viewed_profile")
    return current_user

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.change_password(current_user, payload.current_password, payload.new_password)
    return None
