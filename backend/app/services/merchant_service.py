"""
business logic for merchant creation (auto-generates the first test key pair),
settlement detail updates, and API key issuance/revocation.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_api_key
from app.models.identity import User
from app.models.merchant import ApiKeyType, KycStatus
from app.repositories.identity_repository import IdentityRepository
from app.repositories.merchant_repository import MerchantRepository
from app.schemas.merchant import MerchantCreateRequest, SettlementDetailsRequest, ApiKeyCreatedResponse


class MerchantService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MerchantRepository(db)
        self.identity_repo = IdentityRepository(db)

    def create_merchant_for_user(self, user: User, payload: MerchantCreateRequest):
        if user.merchant_id is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user already owns a merchant account")

        merchant = self.repo.create(
            business_name=payload.business_name,
            business_email=payload.business_email,
            country=payload.country,
            default_currency=payload.default_currency,
        )

        # Link the creating user to their new merchant
        user.merchant_id = merchant.id
        self.db.add(user)
        self.db.commit()

        # Auto-issue a test key pair immediately — this is what makes it Stripe-like:
        # the merchant can start integrating in test mode the same second they sign up.
        self._issue_key_pair(merchant.id, live=False)

        return merchant

    def get_merchant(self, merchant_id: uuid.UUID):
        merchant = self.repo.get_by_id(merchant_id)
        if merchant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
        return merchant

    def update_settlement_details(self, merchant_id: uuid.UUID, payload: SettlementDetailsRequest):
        merchant = self.get_merchant(merchant_id)
        return self.repo.update_settlement_details(
            merchant,
            bank_name=payload.settlement_bank_name,
            account_number=payload.settlement_account_number,
            account_name=payload.settlement_account_name,
        )

    def submit_for_kyc_review(self, merchant_id: uuid.UUID):
        merchant = self.get_merchant(merchant_id)
        if not merchant.settlement_account_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Settlement bank details must be set before submitting for KYC review",
            )
        return self.repo.update_kyc_status(merchant, KycStatus.UNDER_REVIEW)

    def issue_live_keys_if_approved(self, merchant_id: uuid.UUID) -> list[ApiKeyCreatedResponse]:
        merchant = self.get_merchant(merchant_id)
        if merchant.kyc_status != KycStatus.APPROVED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant is not KYC-approved for live mode yet")

        created = []
        created.append(self._issue_key_pair(merchant.id, live=True))
        return created

    def list_api_keys(self, merchant_id: uuid.UUID):
        return self.repo.list_api_keys(merchant_id)

    def revoke_api_key(self, merchant_id: uuid.UUID, api_key_id: uuid.UUID):
        keys = self.repo.list_api_keys(merchant_id)
        target = next((k for k in keys if k.id == api_key_id), None)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
        self.repo.revoke_api_key(target)

    def _issue_key_pair(self, merchant_id: uuid.UUID, live: bool) -> list[ApiKeyCreatedResponse]:
        public_type = ApiKeyType.LIVE_PUBLIC if live else ApiKeyType.TEST_PUBLIC
        secret_type = ApiKeyType.LIVE_SECRET if live else ApiKeyType.TEST_SECRET
        prefix_public = "pk_live" if live else "pk_test"
        prefix_secret = "sk_live" if live else "sk_test"

        results = []
        for key_type, prefix in [(public_type, prefix_public), (secret_type, prefix_secret)]:
            raw_key, display_prefix, hashed_key = generate_api_key(prefix)
            record = self.repo.create_api_key(merchant_id, key_type, display_prefix, hashed_key)
            results.append(
                ApiKeyCreatedResponse(
                    id=record.id,
                    key_type=record.key_type,
                    display_prefix=record.display_prefix,
                    raw_key=raw_key,
                    created_at=record.created_at,
                )
            )
        return results