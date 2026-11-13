from .models import PRODUCTS


COUPON_MULTIPLIERS = {"SAVE10": 0.90, "SAVE5": 0.95}
LOYALTY_MULTIPLIER = 0.98
EXPRESS_FEES = {"remote": 900, "local": 450}
STANDARD_FEES = {"remote": 400, "local": 150}
EXPRESS_DEFAULT_FEE = 650
STANDARD_DEFAULT_FEE = 250
LARGE_ORDER_LIMIT = 15000
LARGE_ORDER_BONUS = 150


def _find_product(product_id):
    product = next((p for p in PRODUCTS if p.id == product_id), None)
    if product is None:
        raise ValueError("Unknown product")
    return product


def _items_subtotal(items):
    subtotal = 0
    for item in items:
        product = _find_product(item["product_id"])
        amount = int(item["quantity"])
        if amount < 1 or amount > product.stock:
            raise ValueError("Incorrect quantity")
        subtotal += product.price * amount
    return subtotal


def _apply_discounts(subtotal, coupon, loyalty):
    if coupon in COUPON_MULTIPLIERS:
        subtotal = int(subtotal * COUPON_MULTIPLIERS[coupon])
    if loyalty:
        subtotal = int(subtotal * LOYALTY_MULTIPLIER)
    return subtotal


def _delivery_fee(express, region):
    if express:
        return EXPRESS_FEES.get(region, EXPRESS_DEFAULT_FEE)
    return STANDARD_FEES.get(region, STANDARD_DEFAULT_FEE)


def calculate_total(items, coupon="", loyalty=False, express=False, region="local"):
    subtotal = _apply_discounts(_items_subtotal(items), coupon, loyalty)
    subtotal += _delivery_fee(express, region)
    if subtotal > LARGE_ORDER_LIMIT and not express:
        subtotal -= LARGE_ORDER_BONUS
    return max(subtotal, 0)


def create_order(items, email, coupon="", loyalty=False):
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    return {"email": email, "items": items, "total": calculate_total(items, coupon, loyalty)}
