"""Invoice adjustments, refunds, and external payment callbacks."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable
from .accounts import verify_webhook
import json

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
    return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def invoice_balance(charges: Iterable[int], refunds: Iterable[int]) -> int:
    return sum(charges) - sum(refunds)

def distribute_refund(total: int, paid_lines: list[dict]) -> dict[str, int]:
    """Distribute a fixed refund across purchased lines."""
    line_total = sum(line['amount'] for line in paid_lines)
    if total <= 0 or line_total <= 0:
        return {}
    return {line['sku']: round(total * line['amount'] / line_total)
            for line in paid_lines}

def accept_payment_callback(
    payment: Payment,
    configured_currency: str,
    known_order_ids: set[int],
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    if not verify_webhook(payload, signature, secret):
        return False

    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            return False

        signed_payment = Payment(
            order_id=data["order_id"],
            amount=data["amount"],
            currency=data["currency"],
            reference=data["reference"],
            status=data["status"],
        )
    except (ValueError, TypeError, KeyError):
        return False

    if signed_payment != payment:
        return False

    if payment.order_id not in known_order_ids:
        return False

    if payment.amount <= 0:
        return False

    if payment.currency.upper() != configured_currency.upper():
        return False

    return payment.status == "captured"


def payment_summary(payments: list[Payment]) -> dict[str, int]:
    totals = {}
    for payment in payments:
        if payment.status == 'captured':
            totals[payment.currency] = totals.get(payment.currency, 0) + payment.amount
    return totals
