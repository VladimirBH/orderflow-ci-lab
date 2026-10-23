"""Invoice adjustments, refunds, and external payment callbacks."""
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from .accounts import verify_webhook

@dataclass(frozen=True)
class Payment:
    order_id: int
    amount: int
    currency: str
    reference: str
    status: str


def convert_minor_units(amount: int, rate: str) -> int:
    """Translate integer minor units using a decimal exchange rate."""
    value = Decimal(amount) * Decimal(rate)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def invoice_balance(charges: Iterable[int], refunds: Iterable[int]) -> int:
    return sum(charges) - sum(refunds)


def distribute_refund(total: int, paid_lines: list[dict]) -> dict[str, int]:
    """Distribute a fixed refund across purchased lines."""
    line_total = sum(line["amount"] for line in paid_lines)
    if total <= 0 or line_total <= 0:
        return {}

    refunds = {}
    remaining = total

    for index, line in enumerate(paid_lines):
        if index == len(paid_lines) - 1:
            amount = remaining
        else:
            amount = round(total * line["amount"] / line_total)
            remaining -= amount

        refunds[line["sku"]] = amount

    return refunds


def accept_payment_callback(
    payload: bytes,
    signature: str,
    secret: str,
    configured_currency: str,
    expected_amounts: dict[int, int],
) -> bool:
    """Accept a provider callback only if it is signed and settles a known order exactly."""
    # Authenticate the raw body ourselves instead of trusting a caller-supplied flag,
    # and build the Payment only from the signed bytes.
    if not verify_webhook(payload, signature, secret):
        return False
    try:
        data = json.loads(payload)
        payment = Payment(data["order_id"], data["amount"], data["currency"], data["reference"], data["status"])
    except (ValueError, KeyError, TypeError):
        return False
    if type(payment.order_id) is not int or type(payment.amount) is not int or not isinstance(payment.currency, str):
        return False
    # The amount must match what the order is due, not merely be positive.
    return (
        payment.status == "captured"
        and payment.amount == expected_amounts.get(payment.order_id)
        and payment.currency.upper() == configured_currency.upper()
    )


def payment_summary(payments: list[Payment]) -> dict[str, int]:
    totals = {}
    for payment in payments:
        if payment.status == "captured":
            totals[payment.currency.upper()] = totals.get(payment.currency.upper(), 0) + payment.amount

    return totals
