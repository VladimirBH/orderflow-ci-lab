import itertools

import pytest

from orderflow.orders import calculate_total

CASES = list(itertools.product(
    [[{"product_id": 2, "quantity": 2}], [{"product_id": 6, "quantity": 5}],
     [{"product_id": 1, "quantity": 6}, {"product_id": 4, "quantity": 3}]],
    ["", "SAVE10", "SAVE5", "UNKNOWN"],
    [False, True],
    [False, True],
    ["local", "remote", "regional"],
))


def reference_total(items, coupon, loyalty, express, region):
    """Original (pre-refactoring) pricing algorithm, kept as an oracle."""
    prices = {1: 2700, 2: 900, 4: 110, 6: 3400}
    subtotal = sum(prices[i["product_id"]] * i["quantity"] for i in items)
    if coupon == "SAVE10":
        subtotal = int(subtotal * 0.90)
    elif coupon == "SAVE5":
        subtotal = int(subtotal * 0.95)
    if loyalty:
        subtotal = int(subtotal * 0.98)
    fees = {(True, "remote"): 900, (True, "local"): 450, (False, "remote"): 400,
            (False, "local"): 150}
    subtotal += fees.get((express, region), 650 if express else 250)
    if subtotal > 15000 and not express:
        subtotal -= 150
    return max(subtotal, 0)


@pytest.mark.parametrize("items,coupon,loyalty,express,region", CASES)
def test_calculate_total_matches_original(items, coupon, loyalty, express, region):
    assert calculate_total(items, coupon, loyalty, express, region) == \
        reference_total(items, coupon, loyalty, express, region)
