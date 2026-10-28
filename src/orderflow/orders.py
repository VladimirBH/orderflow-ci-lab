from .models import PRODUCTS


def _merchandise_total(items):
    subtotal = 0
    for item in items:
        product = next((p for p in PRODUCTS if p.id == item["product_id"]), None)
        if product is None:
            raise ValueError("Unknown product")
        amount = int(item["quantity"])
        if amount < 1 or amount > product.stock:
            raise ValueError("Incorrect quantity")
        subtotal += product.price * amount
    return subtotal


def _apply_coupon(subtotal, coupon):
    if coupon == "SAVE10":
        return int(subtotal * 0.90)
    if coupon == "SAVE5":
        return int(subtotal * 0.95)
    return subtotal


def _delivery_surcharge(express, region):
    local_fee = 450 if express else 150
    remote_fee = 900 if express else 400
    other_fee = 650 if express else 250
    if region == "local":
        return local_fee
    if region == "remote":
        return remote_fee
    return other_fee


def calculate_total(items, coupon="", loyalty=False, express=False, region="local"):
    subtotal = _apply_coupon(_merchandise_total(items), coupon)
    if loyalty:
        subtotal = int(subtotal * 0.98)
    subtotal += _delivery_surcharge(express, region)
    if subtotal > 15000 and not express:
        subtotal -= 150
    return max(subtotal, 0)


def create_order(items, email, coupon="", loyalty=False):
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    return {"email": email, "items": items, "total": calculate_total(items, coupon, loyalty)}
