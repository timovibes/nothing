"""
HTTP routes for merchant creation, viewing, settlement details, KYC submission, and API key
management — all scoped to the logged-in user's own merchant.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.identity import User
from app.services.merchant_service import MerchantService
from app.schemas.merchant import (
    MerchantCreateRequest,
    MerchantResponse,
    SettlementDetailsRequest,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
)
from app.services.team_service import TeamService
from app.schemas.identity import StaffInviteRequest, StaffMemberResponse

router = APIRouter(prefix="/api/v1/merchants", tags=["merchants"])


def _require_merchant_id(user: User) -> uuid.UUID:
    if user.merchant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user has no merchant account yet")
    return user.merchant_id


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
def create_merchant(
    payload: MerchantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = MerchantService(db)
    return service.create_merchant_for_user(current_user, payload)


@router.get("/me", response_model=MerchantResponse)
def get_my_merchant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.get_merchant(merchant_id)


@router.put("/me/settlement-details", response_model=MerchantResponse)
def update_settlement_details(
    payload: SettlementDetailsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.update_settlement_details(merchant_id, payload)


@router.post("/me/submit-kyc", response_model=MerchantResponse)
def submit_kyc(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.submit_for_kyc_review(merchant_id)


@router.post("/me/live-keys", response_model=list[ApiKeyCreatedResponse])
def issue_live_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.issue_live_keys_if_approved(merchant_id)

@router.post("/me/test-keys/regenerate", response_model=list[ApiKeyCreatedResponse])
def regenerate_test_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.regenerate_test_keys(merchant_id)


@router.get("/me/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    return service.list_api_keys(merchant_id)


@router.delete("/me/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant_id = _require_merchant_id(current_user)
    service = MerchantService(db)
    service.revoke_api_key(merchant_id, api_key_id)
    return None

@router.post("/me/staff/invite", response_model=StaffMemberResponse, status_code=status.HTTP_201_CREATED)
def invite_staff(
    payload: StaffInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TeamService(db)
    return service.invite_staff(current_user, payload)


@router.get("/me/staff", response_model=list[StaffMemberResponse])
def list_staff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TeamService(db)
    return service.list_staff(current_user)


@router.delete("/me/staff/{staff_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_staff(
    staff_user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TeamService(db)
    service.remove_staff(current_user, staff_user_id)
    return None