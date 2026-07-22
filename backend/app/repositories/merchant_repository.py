#all direct database queries for merchants and API keys.
import uuid

from sqlalchemy.orm import Session

from app.models.merchant import Merchant, ApiKey, ApiKeyType, KycStatus


class MerchantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, merchant_id: uuid.UUID) -> Merchant | None:
        return self.db.query(Merchant).filter(Merchant.id == merchant_id).first()

    def create(self, business_name: str, business_email: str, country: str, default_currency: str) -> Merchant:
        merchant = Merchant(
            business_name=business_name,
            business_email=business_email,
            country=country,
            default_currency=default_currency,
        )
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant

    def update_settlement_details(self, merchant: Merchant, bank_name: str, account_number: str, account_name: str) -> Merchant:
        merchant.settlement_bank_name = bank_name
        merchant.settlement_account_number = account_number
        merchant.settlement_account_name = account_name
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant

    def update_kyc_status(self, merchant: Merchant, status: KycStatus, rejection_reason: str | None = None) -> Merchant:
        merchant.kyc_status = status
        merchant.kyc_rejection_reason = rejection_reason
        merchant.is_live_mode_enabled = status == KycStatus.APPROVED
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant

    def create_api_key(self, merchant_id: uuid.UUID, key_type: ApiKeyType, display_prefix: str, hashed_key: str) -> ApiKey:
        api_key = ApiKey(
            merchant_id=merchant_id,
            key_type=key_type,
            display_prefix=display_prefix,
            hashed_key=hashed_key,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def list_api_keys(self, merchant_id: uuid.UUID) -> list[ApiKey]:
        return self.db.query(ApiKey).filter(ApiKey.merchant_id == merchant_id).order_by(ApiKey.created_at.desc()).all()

    def get_active_key_by_hash(self, hashed_key: str) -> ApiKey | None:
        return self.db.query(ApiKey).filter(ApiKey.hashed_key == hashed_key, ApiKey.is_active.is_(True)).first()

    def revoke_api_key(self, api_key: ApiKey) -> None:
        from datetime import datetime, timezone
        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        self.db.add(api_key)
        self.db.commit()

    def list_by_kyc_status(self, kyc_status: KycStatus | None = None) -> list[Merchant]:
        query = self.db.query(Merchant)
        if kyc_status is not None:
            query = query.filter(Merchant.kyc_status == kyc_status)
        return query.order_by(Merchant.created_at.desc()).all()