# direct database queries for writing and reading all four audit tables.

import uuid

from sqlalchemy.orm import Session

from app.models.audit import ApiLog, AuditLog, ActivityLog, LoginSession, ActorType


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_api_log(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        ip_address: str | None,
        merchant_id: uuid.UUID | None,
    ) -> ApiLog:
        log = ApiLog(
            merchant_id=merchant_id,
            method=method,
            path=path,
            status_code=status_code,
            latency_ms=latency_ms,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        return log

    def create_audit_log(
        self,
        actor_type: ActorType,
        actor_id: uuid.UUID | None,
        merchant_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        request_body: dict | None,
        status_code: int,
        ip_address: str | None,
    ) -> AuditLog:
        log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            merchant_id=merchant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_body=request_body,
            status_code=status_code,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        return log

    def create_activity_log(self, user_id: uuid.UUID, activity_type: str, metadata: dict | None = None) -> ActivityLog:
        log = ActivityLog(user_id=user_id, activity_type=activity_type, activity_metadata=metadata)
        self.db.add(log)
        self.db.commit()
        return log

    def create_login_session(
        self,
        user_id: uuid.UUID | None,
        email_attempted: str,
        ip_address: str | None,
        device: str | None,
        success: bool,
    ) -> LoginSession:
        session = LoginSession(
            user_id=user_id,
            email_attempted=email_attempted,
            ip_address=ip_address,
            device=device,
            success=success,
        )
        self.db.add(session)
        self.db.commit()
        return session

    def list_audit_logs_for_merchant(self, merchant_id: uuid.UUID, limit: int = 100) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.merchant_id == merchant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_api_logs_for_merchant(self, merchant_id: uuid.UUID, limit: int = 100) -> list[ApiLog]:
        return (
            self.db.query(ApiLog)
            .filter(ApiLog.merchant_id == merchant_id)
            .order_by(ApiLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_all_audit_logs(self, limit: int = 200) -> list[AuditLog]:
        return self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def list_login_sessions_for_user(self, user_id: uuid.UUID, limit: int = 50) -> list[LoginSession]:
        return (
            self.db.query(LoginSession)
            .filter(LoginSession.user_id == user_id)
            .order_by(LoginSession.created_at.desc())
            .limit(limit)
            .all()
        )