from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_client
from app.core.config import settings
from app.core.audit_middleware import AuditMiddleware
from app.api.v1 import auth, merchants, payments, wallet, settlements, refunds, customers, webhooks, notifications, fraud, audit, admin, dashboard

# Import models so SQLAlchemy/Alembic register them against Base.metadata
from app.models import identity, merchant, customer, payment, ledger, settlement, refund, webhook, notification, fraud as fraud_model, audit as audit_model, admin as admin_model  # noqa: F401

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth.router)
app.include_router(merchants.router)
app.include_router(customers.router)
app.include_router(payments.router)
app.include_router(wallet.router)
app.include_router(settlements.router)
app.include_router(refunds.router)
app.include_router(webhooks.router)
app.include_router(notifications.router)
app.include_router(fraud.router)
app.include_router(audit.router)
app.include_router(admin.router)
app.include_router(dashboard.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    checks = {"database": "unknown", "redis": "unknown"}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "not_ready", "checks": checks}