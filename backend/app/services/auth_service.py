"""
The actual business logic for register/login/refresh/logout, plus one-time email
verification at signup. Admin and regular users log in identically — no 2FA at
login, per product decision (deviates from the design doc's §6.6, which called
for mandatory admin OTP-at-login; that requirement was deliberately dropped).
"""

import json
import random
import secrets
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
from app.core.redis import redis_client
from app.repositories.identity_repository import IdentityRepository
from app.repositories.audit_repository import AuditRepository
from app.models.identity import User, UserRole
from app.schemas.identity import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.services.email_adapter import get_email_adapter

EMAIL_VERIFICATION_TTL_SECONDS = 600  # 10 minutes
EMAIL_VERIFICATION_MAX_ATTEMPTS = 5


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

        self._send_verification_email(user.id, user.email)

        return user

    def login(self, payload: UserLoginRequest, ip_address: str | None = None, device: str | None = None) -> TokenResponse:
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

        self.audit_repo.create_login_session(
            user_id=user.id, email_attempted=payload.email, ip_address=ip_address, device=device, success=True
        )
        self.audit_repo.create_activity_log(user_id=user.id, activity_type="login")

        return self._issue_tokens(user.id, user.role.value, user.merchant_id)

    def refresh(self, raw_refresh_token: str) -> TokenResponse:
        hashed = hash_refresh_token(raw_refresh_token)
        token_record = self.repo.get_refresh_token(hashed)

        if token_record is None or not token_record.is_valid():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired")

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

    # --- Email verification (one-time, at signup) ---

    def _send_verification_email(self, user_id: uuid.UUID, email: str) -> None:
        code = f"{random.randint(0, 999999):06d}"
        redis_client.setex(
            f"email_verify:{email.lower()}",
            EMAIL_VERIFICATION_TTL_SECONDS,
            json.dumps({"user_id": str(user_id), "code": code, "attempts": 0}),
        )

        send_result = self.email_adapter.send(
            to_email=email,
            subject="Verify your email",
            body=f"Your verification code is: {code}\n\nThis code expires in 10 minutes.",
        )
        if not send_result.success:
            print(f"[EMAIL VERIFICATION ERROR] Failed to send to {email}: {send_result.error_message}")

    def resend_verification_email(self, email: str) -> None:
        user = self.repo.get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found with this email")
        if user.is_email_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified")
        self._send_verification_email(user.id, user.email)

    def verify_email(self, email: str, code: str) -> None:
        redis_key = f"email_verify:{email.lower()}"
        raw = redis_client.get(redis_key)

        if raw is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired or not found — request a new one")

        data = json.loads(raw)

        if data["attempts"] >= EMAIL_VERIFICATION_MAX_ATTEMPTS:
            redis_client.delete(redis_key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many incorrect attempts — request a new code")

        if code != data["code"]:
            data["attempts"] += 1
            redis_client.setex(redis_key, EMAIL_VERIFICATION_TTL_SECONDS, json.dumps(data))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect code")

        redis_client.delete(redis_key)

        user = self.repo.get_user_by_id(uuid.UUID(data["user_id"]))
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_email_verified = True
        self.db.add(user)
        self.db.commit()

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

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        self.db.add(user)
        self.db.commit()