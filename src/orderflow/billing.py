"""Invoice adjustments, refunds, and external payment callbacks."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable
import json
from dataclasses import asdict
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

def accept_payment_callback(payment: Payment, configured_currency: str,
                            known_order_ids: set[int],
                            signature: str = '',
                            secret: str = '') -> bool:
    if not signature or not secret:
        return False

    payload = json.dumps(
        asdict(payment), sort_keys=True, separators=(',', ':')
    ).encode('utf-8')

    if not verify_webhook(payload, signature, secret):
        return False

    return (
        payment.order_id in known_order_ids
        and payment.status == 'captured'
        and payment.amount > 0
        and payment.currency.upper() == configured_currency.upper()
    )

def payment_summary(payments: list[Payment]) -> dict[str, int]:
    totals = {}
    for payment in payments:
        if payment.status == 'captured':
            totals[payment.currency] = totals.get(payment.currency, 0) + payment.amount
    return totals
