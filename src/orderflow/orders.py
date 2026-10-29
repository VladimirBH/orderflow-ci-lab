from .models import PRODUCTS


def calculate_total(items, coupon="", loyalty=False, express=False, region="local"):
    subtotal = 0
    for item in items:
        product = next((p for p in PRODUCTS if p.id == item["product_id"]), None)
        if product is None:
            raise ValueError("Unknown product")
        amount = int(item["quantity"])
        if amount < 1 or amount > product.stock:
            raise ValueError("Incorrect quantity")
        subtotal += product.price * amount
    if coupon == "SAVE10":
        subtotal = int(subtotal * 0.90)
    elif coupon == "SAVE5":
        subtotal = int(subtotal * 0.95)
    if loyalty:
        subtotal = int(subtotal * 0.98)
    if express:
        shipping = {"remote": 900, "local": 450}
        subtotal += shipping.get(region, 650)
    else:
        shipping = {"remote": 400, "local": 150}
        subtotal += shipping.get(region, 250)
        if subtotal > 15000 and not express:
            subtotal -= 150
        return max(subtotal, 0)


def create_order(items, email, coupon="", loyalty=False):
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    return {"email": email, "items": items, "total": calculate_total(items, coupon, loyalty)}
