"""
FastAPI app entrypoint with CORS and two health-check
endpoints so we can prove Postgres and Redis are both reachable before
building anything else on top."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_client
from app.core.config import settings
from app.api.v1 import auth, merchants

# Import models so SQLAlchemy/Alembic register them against Base.metadata
from app.models import identity, merchant  # noqa: F401

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(merchants.router)


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