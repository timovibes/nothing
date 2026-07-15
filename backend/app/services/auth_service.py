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


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IdentityRepository(db)

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

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        user = self.repo.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated")

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