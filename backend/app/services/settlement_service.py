"""
 the actual settlement business logic — sweeps every merchant's positive balance into a T+2
 in_transit payout (with matching ledger entries), and separately flips due payouts to paid.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.ledger import LedgerAccountType, LedgerEntryDirection, LedgerEntryType
from app.repositories.settlement_repository import SettlementRepository
from app.repositories.ledger_repository import LedgerRepository
from app.services.webhook_service import WebhookService

SETTLEMENT_DELAY_DAYS = 2


class SettlementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SettlementRepository(db)
        self.ledger_repo = LedgerRepository(db)
        self.webhook_service = WebhookService(db)

    def sweep_all_merchant_balances(self) -> list[dict]:
        """
        Pulls every merchant's full available_balance_minor into a new Payout,
        zeroes their available balance, and posts the matching ledger entries:
        platform_cash decreases (credit), merchant_payable decreases (debit) —
        because the platform's obligation to the merchant is now in transit to their bank.
        """
        results = []
        wallets = self.repo.get_all_wallets_with_positive_balance()

        for wallet in wallets:
            amount_to_sweep = wallet.available_balance_minor
            transaction_group_id = uuid.uuid4()
            expected_arrival = datetime.now(timezone.utc) + timedelta(days=SETTLEMENT_DELAY_DAYS)

            # Leg 1: platform cash decreases (credit) — money is leaving the platform's account
            self.ledger_repo.add_entry(
                transaction_group_id=transaction_group_id,
                account_type=LedgerAccountType.PLATFORM_CASH,
                direction=LedgerEntryDirection.CREDIT,
                amount_minor=amount_to_sweep,
                currency=wallet.currency,
                entry_type=LedgerEntryType.PAYOUT,
                merchant_id=wallet.merchant_id,
                description="Funds swept for payout to merchant bank account",
            )

            # Leg 2: merchant_payable decreases (debit) — we no longer owe this, it's in transit
            self.ledger_repo.add_entry(
                transaction_group_id=transaction_group_id,
                account_type=LedgerAccountType.MERCHANT_PAYABLE,
                direction=LedgerEntryDirection.DEBIT,
                amount_minor=amount_to_sweep,
                currency=wallet.currency,
                entry_type=LedgerEntryType.PAYOUT,
                merchant_id=wallet.merchant_id,
                description="Merchant payable cleared, funds now in transit",
            )

            payout = self.repo.create_payout(
                merchant_id=wallet.merchant_id,
                amount_minor=amount_to_sweep,
                currency=wallet.currency,
                expected_arrival_at=expected_arrival,
                ledger_transaction_group_id=transaction_group_id,
            )

            # Zero out the available balance now that it's been swept into a payout
            self.ledger_repo.debit_wallet_for_settlement(wallet.merchant_id, wallet.currency, amount_to_sweep)

            self.db.commit()

            results.append({
                "merchant_id": wallet.merchant_id,
                "payout_id": payout.id,
                "amount_minor": amount_to_sweep,
                "expected_arrival_at": expected_arrival,
            })

        return results

    def process_due_payouts(self, ignore_date_check: bool = False) -> list[uuid.UUID]:
        due_payouts = self.repo.get_due_in_transit_payouts(ignore_date_check=ignore_date_check)
        paid_ids = []

        for payout in due_payouts:
            self.repo.mark_paid(payout)
            paid_ids.append(payout.id)
            self.db.commit()
            self.webhook_service.emit_event(
                payout.merchant_id,
                "payout.paid",
                {
                    "payout_id": str(payout.id),
                    "amount_minor": payout.amount_minor,
                    "currency": payout.currency,
                },
            )

        return paid_ids

    def list_payouts_for_merchant(self, merchant_id: uuid.UUID):
        return self.repo.list_for_merchant(merchant_id)