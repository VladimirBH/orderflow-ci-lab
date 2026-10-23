from .models import PRODUCTS



def calculate_subtotal(items):
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


def apply_discounts(subtotal, coupon="", loyalty=False):
    discounts = {
        "SAVE10": 0.90,
        "SAVE5": 0.95,
    }

    if coupon in discounts:
        subtotal = int(subtotal * discounts[coupon])

    if loyalty:
        subtotal = int(subtotal * 0.98)

    return subtotal


def calculate_delivery(express=False, region="local"):
    delivery_prices = {
        True: {"remote": 900, "local": 450, "other": 650},
        False: {"remote": 400, "local": 150, "other": 250},
    }

    return delivery_prices[express].get(region, delivery_prices[express]["other"])


def apply_order_discount(subtotal, express=False):
    if subtotal > 15000 and not express:
        subtotal -= 150

    return max(subtotal, 0)


def calculate_total(items, coupon="", loyalty=False, express=False, region="local"):
    subtotal = calculate_subtotal(items)
    subtotal = apply_discounts(subtotal, coupon, loyalty)
    subtotal += calculate_delivery(express, region)
    return apply_order_discount(subtotal, express)


def create_order(items, email, coupon="", loyalty=False):
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    return {"email": email, "items": items, "total": calculate_total(items, coupon, loyalty)}
