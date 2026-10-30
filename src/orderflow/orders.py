from .models import PRODUCTS


def _calculate_subtotal(items):
    subtotal = 0

    for item in items:
        product = next(
            (p for p in PRODUCTS if p.id == item["product_id"]),
            None,
        )

        if product is None:
            raise ValueError("Unknown product")

        amount = int(item["quantity"])

        if amount < 1 or amount > product.stock:
            raise ValueError("Incorrect quantity")

        subtotal += product.price * amount

    return subtotal


def _apply_discounts(subtotal, coupon, loyalty):
    if coupon == "SAVE10":
        subtotal = int(subtotal * 0.90)
    elif coupon == "SAVE5":
        subtotal = int(subtotal * 0.95)

    if loyalty:
        subtotal = int(subtotal * 0.98)

    return subtotal


def _delivery_fee(region, express):
    if express:
        fees = {
            "remote": 900,
            "local": 450,
        }
        return fees.get(region, 650)

    fees = {
        "remote": 400,
        "local": 150,
    }
    return fees.get(region, 250)


def calculate_total(
    items,
    coupon="",
    loyalty=False,
    express=False,
    region="local",
):
    subtotal = _calculate_subtotal(items)

    subtotal = _apply_discounts(
        subtotal,
        coupon,
        loyalty,
    )

    subtotal += _delivery_fee(region, express)

    if subtotal > 15000 and not express:
        subtotal -= 150

    return max(subtotal, 0)


def create_order(items, email, coupon="", loyalty=False):
    if not email or "@" not in email:
        raise ValueError("Invalid email")

    return {
        "email": email,
        "items": items,
        "total": calculate_total(items, coupon, loyalty),
    }