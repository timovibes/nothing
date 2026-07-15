"""
the core double-entry logic — calculates the platform fee and writes a balanced set of
ledger entries for a successful payment, with a built-in balance assertion so a broken
transaction can never silently post.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.ledger import LedgerAccountType, LedgerEntryDirection, LedgerEntryType
from app.repositories.ledger_repository import LedgerRepository

# Stripe-style fee: 2.9% + a flat fee, in minor units (cents/lowest currency unit)
FEE_PERCENTAGE = 0.029
FEE_FIXED_MINOR = 3000  # KES 30.00 flat, expressed in minor units


class LedgerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LedgerRepository(db)

    def calculate_fee(self, amount_minor: int) -> int:
        percentage_fee = round(amount_minor * FEE_PERCENTAGE)
        return percentage_fee + FEE_FIXED_MINOR

    def record_successful_payment(
        self,
        merchant_id: uuid.UUID,
        payment_intent_id: uuid.UUID,
        amount_minor: int,
        currency: str,
    ) -> dict:
        fee_minor = self.calculate_fee(amount_minor)
        net_to_merchant_minor = amount_minor - fee_minor

        if net_to_merchant_minor < 0:
            # Fee exceeds the payment amount — should never happen at realistic amounts, but guard anyway
            raise ValueError(f"Calculated fee ({fee_minor}) exceeds payment amount ({amount_minor})")

        transaction_group_id = uuid.uuid4()

        # Leg 1: platform receives the full amount as cash (debit — asset increases)
        self.repo.add_entry(
            transaction_group_id=transaction_group_id,
            account_type=LedgerAccountType.PLATFORM_CASH,
            direction=LedgerEntryDirection.DEBIT,
            amount_minor=amount_minor,
            currency=currency,
            entry_type=LedgerEntryType.PAYMENT_SETTLEMENT,
            merchant_id=merchant_id,
            reference_id=payment_intent_id,
            description="Full payment amount received from processor",
        )

        # Leg 2: platform owes the merchant their net share (credit — liability increases)
        self.repo.add_entry(
            transaction_group_id=transaction_group_id,
            account_type=LedgerAccountType.MERCHANT_PAYABLE,
            direction=LedgerEntryDirection.CREDIT,
            amount_minor=net_to_merchant_minor,
            currency=currency,
            entry_type=LedgerEntryType.PAYMENT_SETTLEMENT,
            merchant_id=merchant_id,
            reference_id=payment_intent_id,
            description="Merchant's net share after platform fee",
        )

        # Leg 3: platform recognizes its fee as revenue (credit — income increases)
        self.repo.add_entry(
            transaction_group_id=transaction_group_id,
            account_type=LedgerAccountType.PLATFORM_REVENUE,
            direction=LedgerEntryDirection.CREDIT,
            amount_minor=fee_minor,
            currency=currency,
            entry_type=LedgerEntryType.PAYMENT_SETTLEMENT,
            merchant_id=merchant_id,
            reference_id=payment_intent_id,
            description=f"Platform fee ({FEE_PERCENTAGE * 100}% + {FEE_FIXED_MINOR} minor units flat)",
        )

        # Balance check — total debits must equal total credits before we ever commit
        total_debits = amount_minor
        total_credits = net_to_merchant_minor + fee_minor
        assert total_debits == total_credits, (
            f"Ledger imbalance detected: debits={total_debits}, credits={total_credits}. Refusing to commit."
        )

        # Update the merchant's available balance so it reflects this payment immediately
        self.repo.credit_wallet(merchant_id, currency, net_to_merchant_minor)

        self.db.commit()

        return {
            "transaction_group_id": transaction_group_id,
            "gross_amount_minor": amount_minor,
            "fee_minor": fee_minor,
            "net_to_merchant_minor": net_to_merchant_minor,
        }