from orderflow.fulfillment import Basket, Line, reserve_items


def test_reserve_exact_available_stock_boundary():
    stock = {"SKU-1": 3}
    basket = Basket(1, [Line("SKU-1", 3, 500, "office")])

    assert reserve_items(basket, stock) is True
    assert stock == {"SKU-1": 0}


def test_reserve_rolls_back_when_a_later_line_cannot_be_satisfied():
    stock = {"SKU-1": 5}
    basket = Basket(
        1,
        [Line("SKU-1", 3, 500, "office"), Line("SKU-1", 3, 500, "office")],
    )

    original_stock = dict(stock)
    assert reserve_items(basket, stock) is False
    assert stock == original_stock
