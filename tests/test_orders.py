import pytest
from orderflow.orders import calculate_total, create_order


def test_total_local():
    assert calculate_total([{"product_id": 2, "quantity": 2}]) == 1950


def test_total_coupon():
    assert calculate_total([{"product_id": 1, "quantity": 1}], coupon="SAVE10") == 2580


def test_unknown_item():
    with pytest.raises(ValueError):
        calculate_total([{"product_id": 99, "quantity": 1}])


def test_create_order():
    assert create_order([{"product_id": 3, "quantity": 1}], "student@example.test")["total"] == 470


@pytest.mark.parametrize(
    "region, express, expected_fee",
    [
        ("local", False, 150),
        ("remote", False, 400),
        ("other", False, 250),
        ("local", True, 450),
        ("remote", True, 900),
        ("other", True, 650),
    ],
)
def test_delivery_fees(region, express, expected_fee):
    from orderflow.orders import _delivery_fee

    assert _delivery_fee(region, express) == expected_fee


def test_coupon_and_loyalty_order():
    from orderflow.orders import _apply_discounts

    result = _apply_discounts(
        subtotal=10000,
        coupon="SAVE10",
        loyalty=True,
    )

    assert result == 8820


def test_unknown_coupon_does_not_apply_discount():
    from orderflow.orders import _apply_discounts

    assert _apply_discounts(10000, "UNKNOWN", False) == 10000
