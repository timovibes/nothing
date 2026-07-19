"""
JWT-authenticated read endpoints purpose-built for the browser dashboard — same underlying
services as the API-key routes, but resolving the merchant from the logged-in user's session
instead of a secret key.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.identity import User
from app.repositories.ledger_repository import LedgerRepository
from app.services.payment_service import PaymentService
from app.services.settlement_service import SettlementService
from app.schemas.payment import PaymentIntentResponse
from app.schemas.ledger import WalletBalanceResponse
from app.schemas.settlement import PayoutResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _require_merchant_id(user: User) -> uuid.UUID:
    if user.merchant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user has no merchant account yet")
    return user.merchant_id


@router.get("/wallet-balance", response_model=list[WalletBalanceResponse])
def get_wallet_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    repo = LedgerRepository(db)
    wallet = repo.get_or_create_wallet(merchant_id, current_user.merchant.default_currency)
    db.commit()
    return [wallet]


@router.get("/payment-intents", response_model=list[PaymentIntentResponse])
def list_payment_intents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = PaymentService(db)
    return service.list_intents(merchant_id)


@router.get("/payouts", response_model=list[PayoutResponse])
def list_payouts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant_id = _require_merchant_id(current_user)
    service = SettlementService(db)
    return service.list_payouts_for_merchant(merchant_id)