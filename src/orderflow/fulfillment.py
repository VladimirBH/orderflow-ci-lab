"""High-level order acceptance and stock reservation."""
from dataclasses import dataclass, field
from .promotions import apply_promotions, calculate_service_fee

@dataclass
class Line:
    sku: str
    quantity: int
    unit_price: int
    category: str

@dataclass
class Basket:
    user_id: int
    lines: list[Line] = field(default_factory=list)
    coupon_codes: list[str] = field(default_factory=list)

def calculate_invoice(basket: Basket, delivery='pickup', loyalty='standard'):
    subtotal = sum(line.quantity * line.unit_price for line in basket.lines)
    discounted, applied = apply_promotions(subtotal, basket.coupon_codes,
                                            [line.category for line in basket.lines])
    handling_fee = calculate_service_fee(discounted, loyalty, delivery)
    return {'subtotal': subtotal, 'discounted': discounted,
            'applied': applied, 'handling_fee': handling_fee,
            'total': discounted + handling_fee}

def reserve_items(basket: Basket, stock: dict[str, int]):
    requested: dict[str, int] = {}
    for line in basket.lines:
        if line.quantity <= 0:
            raise ValueError('Invalid quantity')
        requested[line.sku] = requested.get(line.sku, 0) + line.quantity

    for sku, quantity in requested.items():
        if stock.get(sku, 0) < quantity:
            return False

    for sku, quantity in requested.items():
        stock[sku] -= quantity
    return True

def refund_amount(invoice: dict, delivered: bool, restocking: bool):
    total = invoice['total']
    if delivered and restocking:
        total -= int(invoice['discounted'] * .05)
    return max(0, total)
