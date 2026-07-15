"""
the PaymentProcessorAdapter interface plus our internal sandbox simulator
implementation — this is the single swappable boundary a real Stripe/Flutterwave adapter would
replace later, without touching anything else in the system.
"""

import random
import string
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class AuthorizationOutcome(str, Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    TIMEOUT = "timeout"


@dataclass
class TokenizeResult:
    token: str
    card_brand: str
    card_last4: str


@dataclass
class AuthorizationResult:
    outcome: AuthorizationOutcome
    processor_reference: str
    failure_reason: str | None = None


class PaymentProcessorAdapter(ABC):
    """
    Any real processor (Stripe, Flutterwave, Paystack) implements this exact interface.
    Nothing else in the system — ledger, webhooks, fraud checks, settlement — depends on
    which implementation is plugged in here. Swap the adapter, keep everything else.
    """

    @abstractmethod
    def tokenize_card(self, card_number: str, exp_month: int, exp_year: int, cvv: str) -> TokenizeResult:
        ...

    @abstractmethod
    def authorize(self, amount_minor: int, currency: str, payment_method_token: str) -> AuthorizationResult:
        ...


def _detect_brand(card_number: str) -> str:
    if card_number.startswith("4"):
        return "visa"
    if card_number.startswith(("51", "52", "53", "54", "55")):
        return "mastercard"
    if card_number.startswith("506"):
        return "verve"
    return "unknown"


class SandboxProcessorAdapter(PaymentProcessorAdapter):
    """
    Internal simulator — no external network calls, no external account.
    Decline/timeout behavior is driven entirely by the payment amount's minor-unit ending,
    which keeps testing deterministic and memorable:
      ...00 -> approved
      ...01 -> declined (insufficient funds)
      ...02 -> declined (card blocked)
      ...03 -> timeout
      anything else -> approved
    """

    def tokenize_card(self, card_number: str, exp_month: int, exp_year: int, cvv: str) -> TokenizeResult:
        digits_only = "".join(ch for ch in card_number if ch.isdigit())
        token = "tok_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        return TokenizeResult(
            token=token,
            card_brand=_detect_brand(digits_only),
            card_last4=digits_only[-4:] if len(digits_only) >= 4 else digits_only,
        )

    def authorize(self, amount_minor: int, currency: str, payment_method_token: str) -> AuthorizationResult:
        reference = f"sbx_{uuid.uuid4().hex[:16]}"
        last_two_digits = amount_minor % 100

        if last_two_digits == 1:
            return AuthorizationResult(
                outcome=AuthorizationOutcome.DECLINED,
                processor_reference=reference,
                failure_reason="insufficient_funds",
            )
        if last_two_digits == 2:
            return AuthorizationResult(
                outcome=AuthorizationOutcome.DECLINED,
                processor_reference=reference,
                failure_reason="card_blocked",
            )
        if last_two_digits == 3:
            return AuthorizationResult(
                outcome=AuthorizationOutcome.TIMEOUT,
                processor_reference=reference,
                failure_reason="processor_timeout",
            )

        return AuthorizationResult(outcome=AuthorizationOutcome.APPROVED, processor_reference=reference)


def get_processor_adapter() -> PaymentProcessorAdapter:
    # Swap this single line to plug in a real processor later (e.g. StripeAdapter()).
    return SandboxProcessorAdapter()