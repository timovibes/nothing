"""
HTTP routes for a merchant to check their wallet balance and view their ledger
history — authenticated via secret API key, same as payments.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.repositories.ledger_repository import LedgerRepository
from app.schemas.ledger import WalletBalanceResponse, LedgerEntryResponse

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


@router.get("/balance", response_model=list[WalletBalanceResponse])
def get_balances(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    repo = LedgerRepository(db)
    wallet = repo.get_or_create_wallet(auth.merchant.id, auth.merchant.default_currency)
    db.commit()
    return [wallet]


@router.get("/ledger", response_model=list[LedgerEntryResponse])
def get_ledger_history(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    repo = LedgerRepository(db)
    return repo.get_entries_for_merchant(auth.merchant.id)