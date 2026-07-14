"""
password hashing, JWT access/refresh token creation and verification, and API key
generation/hashing — all the cryptographic primitives auth will depend on.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Password hashing ----------

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- JWT access / refresh tokens ----------

def create_access_token(subject: str, role: str, merchant_id: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "merchant_id": merchant_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token_value() -> str:
    # Opaque random token — the raw value is only ever returned to the client once.
    # We store only its hash (see hash_refresh_token) in the refresh_tokens table.
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------- API keys ----------

def generate_api_key(prefix: str) -> tuple[str, str, str]:
    """
    Returns (raw_key, key_prefix_for_display, hashed_key).
    raw_key is shown to the merchant exactly once. Only hashed_key is stored.
    prefix should be one of: 'pk_live', 'pk_test', 'sk_live', 'sk_test'
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}_{random_part}"
    display_prefix = raw_key[:12]
    hashed_key = hash_api_key(raw_key)
    return raw_key, display_prefix, hashed_key


def hash_api_key(raw_key: str) -> str:
    # Peppered hash: even if the DB leaks, keys can't be brute-forced without API_KEY_PEPPER
    return hashlib.sha256(f"{raw_key}{settings.API_KEY_PEPPER}".encode()).hexdigest()