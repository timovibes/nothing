"""
the API-key authentication dependency for payment endpoints — verifies the merchant's
sk_test/sk_live secret key and resolves it to a merchant, separate from the JWT dashboard auth.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.merchant import Merchant, ApiKeyType
from app.repositories.merchant_repository import MerchantRepository

api_key_scheme = HTTPBearer()


class AuthenticatedMerchant:
    def __init__(self, merchant: Merchant, is_live_mode: bool):
        self.merchant = merchant
        self.is_live_mode = is_live_mode


def get_merchant_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedMerchant:
    raw_key = credentials.credentials

    if not (raw_key.startswith("sk_test_") or raw_key.startswith("sk_live_")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payment endpoints require a secret API key (sk_test_... or sk_live_...), not a dashboard token",
        )

    hashed = hash_api_key(raw_key)
    repo = MerchantRepository(db)
    api_key_record = repo.get_active_key_by_hash(hashed)

    if api_key_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API key")

    merchant = repo.get_by_id(api_key_record.merchant_id)
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Merchant for this API key no longer exists")

    is_live = api_key_record.key_type == ApiKeyType.LIVE_SECRET

    if is_live and not merchant.is_live_mode_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Live mode is not enabled for this merchant yet")

    return AuthenticatedMerchant(merchant=merchant, is_live_mode=is_live)