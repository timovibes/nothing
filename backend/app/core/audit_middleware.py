"""
ASGI middleware that automatically logs every request to api_logs, and every mutating request
(POST/PUT/PATCH/DELETE) to audit_logs with a sanitized copy of the request body — applies to
the entire app with zero per-endpoint code.
"""

import json
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.database import SessionLocal
from app.core.security import decode_access_token, hash_api_key
from app.models.audit import ActorType
from app.repositories.audit_repository import AuditRepository
from app.repositories.merchant_repository import MerchantRepository

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Field names stripped from any logged request body — never store secrets in an audit trail
SENSITIVE_FIELDS = {"password", "card_number", "cvv", "raw_key", "refresh_token", "access_token"}

UUID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def sanitize_body(data):
    if isinstance(data, dict):
        return {
            key: ("***REDACTED***" if key in SENSITIVE_FIELDS else sanitize_body(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [sanitize_body(item) for item in data]
    return data


def parse_entity_from_path(path: str) -> tuple[str, uuid.UUID | None]:
    segments = [s for s in path.split("/") if s]
    entity_type = segments[2] if len(segments) > 2 else "unknown"  # segments[0]="api", [1]="v1", [2]=resource

    entity_id = None
    for segment in segments:
        if UUID_PATTERN.fullmatch(segment):
            entity_id = uuid.UUID(segment)
            break

    return entity_type, entity_id


async def resolve_actor(request: Request, db) -> tuple[ActorType, uuid.UUID | None, uuid.UUID | None]:
    """Returns (actor_type, actor_id, merchant_id) — best-effort, never raises."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return ActorType.ANONYMOUS, None, None

    token = auth_header[len("Bearer "):]

    if token.startswith("sk_test_") or token.startswith("sk_live_"):
        try:
            hashed = hash_api_key(token)
            repo = MerchantRepository(db)
            api_key_record = repo.get_active_key_by_hash(hashed)
            if api_key_record:
                return ActorType.MERCHANT_API_KEY, api_key_record.merchant_id, api_key_record.merchant_id
        except Exception:
            pass
        return ActorType.ANONYMOUS, None, None

    payload = decode_access_token(token)
    if payload:
        try:
            user_id = uuid.UUID(payload.get("sub"))
            merchant_id = uuid.UUID(payload["merchant_id"]) if payload.get("merchant_id") else None
            return ActorType.USER, user_id, merchant_id
        except (ValueError, TypeError):
            pass

    return ActorType.ANONYMOUS, None, None


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"[AUDIT TRACE] 1. dispatch started: {request.method} {request.url.path}")
        start_time = time.perf_counter()

        body_bytes = b""
        if request.method in MUTATING_METHODS:
            print("[AUDIT TRACE] 2. reading body...")
            body_bytes = await request.body()
            print(f"[AUDIT TRACE] 3. body read, {len(body_bytes)} bytes")

            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive

        print("[AUDIT TRACE] 4. calling downstream app...")
        response = await call_next(request)
        print(f"[AUDIT TRACE] 5. downstream returned status {response.status_code}")

        latency_ms = (time.perf_counter() - start_time) * 1000
        ip_address = request.client.host if request.client else None
        path = request.url.path

        if path.startswith("/docs") or path.startswith("/openapi") or path in ("/healthz", "/readyz"):
            print("[AUDIT TRACE] 6. skipped — excluded path")
            return response

        print("[AUDIT TRACE] 7. opening db session...")
        db = SessionLocal()
        try:
            print("[AUDIT TRACE] 8. resolving actor...")
            actor_type, actor_id, merchant_id = await resolve_actor(request, db)
            print(f"[AUDIT TRACE] 9. actor resolved: {actor_type}, merchant_id={merchant_id}")

            audit_repo = AuditRepository(db)

            print("[AUDIT TRACE] 10. writing api_log...")
            audit_repo.create_api_log(
                method=request.method,
                path=path,
                status_code=response.status_code,
                latency_ms=latency_ms,
                ip_address=ip_address,
                merchant_id=merchant_id,
            )
            print("[AUDIT TRACE] 11. api_log written OK")

            if request.method in MUTATING_METHODS:
                print("[AUDIT TRACE] 12. writing audit_log...")
                entity_type, entity_id = parse_entity_from_path(path)
                parsed_body = None
                if body_bytes:
                    try:
                        parsed_body = sanitize_body(json.loads(body_bytes))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        parsed_body = None

                audit_repo.create_audit_log(
                    actor_type=actor_type,
                    actor_id=actor_id,
                    merchant_id=merchant_id,
                    action=request.method,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    request_body=parsed_body,
                    status_code=response.status_code,
                    ip_address=ip_address,
                )
                print("[AUDIT TRACE] 13. audit_log written OK")
        except Exception as e:
            print(f"[AUDIT TRACE] !!! EXCEPTION: {type(e).__name__}: {e}")
        finally:
            db.close()
            print("[AUDIT TRACE] 14. db closed, dispatch complete")

        return response