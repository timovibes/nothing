"""
Merchant staff invitation, listing, and removal. Mirrors AuthService's email-verification
pattern: an invite token lives in Redis with a TTL, gets emailed as a link, and is consumed
once to activate the staff account. Only a merchant_owner may invite or remove staff.
"""

import json
import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.redis import redis_client
from app.repositories.identity_repository import IdentityRepository
from app.models.identity import UserRole, User
from app.schemas.identity import StaffInviteRequest, AcceptInviteRequest
from app.services.email_adapter import get_email_adapter

INVITE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
FRONTEND_BASE_URL = "http://localhost:5173"  # matches the Vite dev server used throughout this build


def _require_owner(user: User) -> uuid.UUID:
    if user.role != UserRole.MERCHANT_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the merchant owner can manage staff")
    if user.merchant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user has no merchant account yet")
    return user.merchant_id


class TeamService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IdentityRepository(db)
        self.email_adapter = get_email_adapter()

    def invite_staff(self, owner: User, payload: StaffInviteRequest):
        merchant_id = _require_owner(owner)

        existing = self.repo.get_user_by_email(payload.email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

        # Placeholder password: unusable until accept-invite sets a real one, since
        # hashed_password is NOT NULL and is_active=False blocks login in the meantime anyway.
        placeholder = hash_password(secrets.token_urlsafe(32))
        user = self.repo.create_staff_invite_user(
            email=payload.email,
            full_name=payload.full_name,
            merchant_id=merchant_id,
            placeholder_hashed_password=placeholder,
        )

        token = secrets.token_urlsafe(32)
        redis_client.setex(
            f"staff_invite:{token}",
            INVITE_TTL_SECONDS,
            json.dumps({"user_id": str(user.id)}),
        )

        invite_link = f"{FRONTEND_BASE_URL}/accept-invite?token={token}"
        send_result = self.email_adapter.send(
            to_email=payload.email,
            subject=f"You've been invited to join {owner.merchant.business_name} on nothing",
            body=f"You've been invited to join {owner.merchant.business_name}'s team.\n\n"
                 f"Set your password here: {invite_link}\n\nThis link expires in 7 days.",
        )
        if not send_result.success:
            print(f"[STAFF INVITE EMAIL ERROR] Failed to send to {payload.email}: {send_result.error_message}")

        return user

    def list_staff(self, owner: User):
        merchant_id = _require_owner(owner)
        return self.repo.list_staff_for_merchant(merchant_id)

    def remove_staff(self, owner: User, staff_user_id: uuid.UUID) -> None:
        merchant_id = _require_owner(owner)
        staff_user = self.repo.get_user_by_id(staff_user_id)
        if staff_user is None or staff_user.merchant_id != merchant_id or staff_user.role != UserRole.MERCHANT_STAFF:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
        self.repo.deactivate_user(staff_user)

    def accept_invite(self, payload: AcceptInviteRequest):
        redis_key = f"staff_invite:{payload.token}"
        raw = redis_client.get(redis_key)
        if raw is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invite link is invalid or has expired")

        data = json.loads(raw)
        user = self.repo.get_user_by_id(uuid.UUID(data["user_id"]))
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited user not found")

        redis_client.delete(redis_key)
        hashed = hash_password(payload.password)
        return self.repo.activate_staff_user(user, hashed)