"""
all direct database queries for users and refresh tokens, kept separate from
business logic so services never write raw SQLAlchemy queries themselves.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.identity import User, RefreshToken, UserRole


class IdentityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.MERCHANT_OWNER,
        merchant_id: uuid.UUID | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            merchant_id=merchant_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def store_refresh_token(self, user_id: uuid.UUID, hashed_token: str, expires_in_days: int) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            hashed_token=hashed_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_refresh_token(self, hashed_token: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).filter(RefreshToken.hashed_token == hashed_token).first()

    def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        self.db.add(token)
        self.db.commit()

    def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})
        self.db.commit()