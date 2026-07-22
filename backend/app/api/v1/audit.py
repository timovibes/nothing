"""
merchant-facing views into their own API/audit logs (secret key), plus a login history endpoint
(dashboard JWT) and an admin-only global audit feed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.models.identity import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import ApiLogResponse, AuditLogResponse, LoginSessionResponse
from app.schemas.identity import AcceptInviteRequest, StaffMemberResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/api-logs", response_model=list[ApiLogResponse])
def list_api_logs(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    repo = AuditRepository(db)
    return repo.list_api_logs_for_merchant(auth.merchant.id)


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    repo = AuditRepository(db)
    return repo.list_audit_logs_for_merchant(auth.merchant.id)


@router.get("/login-history", response_model=list[LoginSessionResponse])
def list_login_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = AuditRepository(db)
    return repo.list_login_sessions_for_user(current_user.id)


@router.get("/audit-logs/all", response_model=list[AuditLogResponse], tags=["audit-admin"])
def list_all_audit_logs(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = AuditRepository(db)
    return repo.list_all_audit_logs()

@router.post("/accept-invite", response_model=StaffMemberResponse)
def accept_invite(payload: AcceptInviteRequest, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.accept_invite(payload)