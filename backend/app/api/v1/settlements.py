"""
HTTP routes for viewing payout history (real merchant-facing endpoint) plus two clearly-marked
test-only endpoints to manually trigger the sweep and force-process payouts without waiting for
Celery Beat's schedule or the real T+2 delay.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps_apikey import get_merchant_from_api_key, AuthenticatedMerchant
from app.services.settlement_service import SettlementService
from app.schemas.settlement import PayoutResponse

router = APIRouter(prefix="/api/v1/settlements", tags=["settlements"])


@router.get("/payouts", response_model=list[PayoutResponse])
def list_payouts(
    auth: AuthenticatedMerchant = Depends(get_merchant_from_api_key),
    db: Session = Depends(get_db),
):
    service = SettlementService(db)
    return service.list_payouts_for_merchant(auth.merchant.id)


# --- TEST-ONLY ENDPOINTS ---
# These exist purely so we can verify the settlement flow without waiting for Celery Beat's
# real schedule or the real T+2 day delay. Remove or lock these behind an admin/internal-only
# guard before any real deployment.

@router.post("/test/trigger-sweep", tags=["settlements-test-only"])
def test_trigger_sweep(db: Session = Depends(get_db)):
    service = SettlementService(db)
    results = service.sweep_all_merchant_balances()
    return {"swept": results}


@router.post("/test/force-process-payouts", tags=["settlements-test-only"])
def test_force_process_payouts(db: Session = Depends(get_db)):
    service = SettlementService(db)
    paid_ids = service.process_due_payouts(ignore_date_check=True)
    return {"paid_payout_ids": paid_ids}