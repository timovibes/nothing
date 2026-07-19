"""
the actual business logic for register/login/refresh/logout like password checks,
token issuance, and refresh-token rotation.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token_value,
    hash_refresh_token,
)
from app.core.config import settings
from app.repositories.identity_repository import IdentityRepository
from app.models.identity import UserRole
from app.schemas.identity import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.repositories.audit_repository import AuditRepository
import json
import random
import secrets

from app.core.redis import redis_client
from app.services.email_adapter import get_email_adapter
from app.schemas.identity import OtpRequiredResponse, VerifyOtpRequest

OTP_TTL_SECONDS = 300  # 5 minutes
OTP_MAX_ATTEMPTS = 5


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IdentityRepository(db)
        self.audit_repo = AuditRepository(db)
        self.email_adapter = get_email_adapter()

    def register(self, payload: UserRegisterRequest):
        existing = self.repo.get_user_by_email(payload.email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

        hashed = hash_password(payload.password)
        user = self.repo.create_user(
            email=payload.email,
            hashed_password=hashed,
            full_name=payload.full_name,
            role=UserRole.MERCHANT_OWNER,
        )
        return user

    def login(self, payload: UserLoginRequest, ip_address: str | None = None, device: str | None = None):
        user = self.repo.get_user_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            self.audit_repo.create_login_session(
                user_id=user.id if user else None,
                email_attempted=payload.email,
                ip_address=ip_address,
                device=device,
                success=False,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        if not user.is_active:
            self.audit_repo.create_login_session(
                user_id=user.id, email_attempted=payload.email, ip_address=ip_address, device=device, success=False
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated")

        # Admins require a second factor before a real session is issued — password alone isn't enough
        if user.role == UserRole.ADMIN:
            return self._start_admin_otp_challenge(user)

        self.audit_repo.create_login_session(
            user_id=user.id, email_attempted=payload.email, ip_address=ip_address, device=device, success=True
        )
        self.audit_repo.create_activity_log(user_id=user.id, activity_type="login")

        return self._issue_tokens(user.id, user.role.value, user.merchant_id)

    def _start_admin_otp_challenge(self, user) -> OtpRequiredResponse:
        code = f"{random.randint(0, 999999):06d}"
        otp_session_id = secrets.token_urlsafe(24)

        redis_client.setex(
            f"admin_otp:{otp_session_id}",
            OTP_TTL_SECONDS,
            json.dumps({"user_id": str(user.id), "code": code, "attempts": 0}),
        )

        self.email_adapter.send(
            to_email=user.email,
            subject="Your admin login code",
            body=f"Your PayFlow admin login code is: {code}\n\nThis code expires in 5 minutes. If you didn't request this, ignore this email.",
        )

        return OtpRequiredResponse(otp_session_id=otp_session_id)

    def verify_otp(self, payload: VerifyOtpRequest, ip_address: str | None = None, device: str | None = None) -> TokenResponse:
        redis_key = f"admin_otp:{payload.otp_session_id}"
        raw = redis_client.get(redis_key)

        if raw is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP session expired or invalid — please log in again")

        data = json.loads(raw)

        if data["attempts"] >= OTP_MAX_ATTEMPTS:
            redis_client.delete(redis_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Too many incorrect attempts — please log in again")

        if payload.code != data["code"]:
            data["attempts"] += 1
            redis_client.setex(redis_key, OTP_TTL_SECONDS, json.dumps(data))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect code")

        redis_client.delete(redis_key)

        user_id = uuid.UUID(data["user_id"])
        user = self.repo.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer active")

        self.audit_repo.create_login_session(
            user_id=user.id, email_attempted=user.email, ip_address=ip_address, device=device, success=True
        )
        self.audit_repo.create_activity_log(user_id=user.id, activity_type="login")

        return self._issue_tokens(user.id, user.role.value, user.merchant_id)

    def refresh(self, raw_refresh_token: str) -> TokenResponse:
        hashed = hash_refresh_token(raw_refresh_token)
        token_record = self.repo.get_refresh_token(hashed)

        if token_record is None or not token_record.is_valid():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired")

        # Rotate: kill the old token the instant it's used, issue a brand new pair
        self.repo.revoke_refresh_token(token_record)

        user = self.repo.get_user_by_id(token_record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer active")

        return self._issue_tokens(user.id, user.role.value, user.merchant_id)

    def logout(self, raw_refresh_token: str) -> None:
        hashed = hash_refresh_token(raw_refresh_token)
        token_record = self.repo.get_refresh_token(hashed)
        if token_record is not None and token_record.is_valid():
            self.repo.revoke_refresh_token(token_record)

    def _issue_tokens(self, user_id: uuid.UUID, role: str, merchant_id: uuid.UUID | None) -> TokenResponse:
        access_token = create_access_token(subject=str(user_id), role=role, merchant_id=str(merchant_id) if merchant_id else None)

        raw_refresh = create_refresh_token_value()
        hashed_refresh = hash_refresh_token(raw_refresh)
        self.repo.store_refresh_token(
            user_id=user_id,
            hashed_token=hashed_refresh,
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )

        return TokenResponse(access_token=access_token, refresh_token=raw_refresh)