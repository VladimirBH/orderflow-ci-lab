from datetime import datetime, timezone
from orderflow.access import Principal, can_view_order, safe_return_url
from orderflow.billing import Payment, payment_summary, convert_minor_units
from orderflow.customers import Customer, segment
from orderflow.inventory import Warehouse, allocate_order, release_order
from orderflow.notifications import retry_delays
from orderflow.settlement import reconcile, sum_by_merchant


def test_payment_reporting():
    payments = [Payment(1, 1500, "RUB", "x1", "captured"), Payment(2, 500, "RUB", "x2", "failed")]
    assert payment_summary(payments) == {"RUB": 1500}
    assert convert_minor_units(100, "1.25") == 125

def test_inventory_single_sku():
    warehouse = Warehouse({"A": 5})
    assert allocate_order(warehouse, "ORD-1", [{"sku": "A", "quantity": 2}])
    assert warehouse.available["A"] == 3
    release_order(warehouse, "ORD-1")
    assert warehouse.available["A"] == 5

def test_access_customer():
    customer = Principal(4, "user", 1)
    assert can_view_order(customer, {"owner_id": 4, "tenant_id": 1})
    assert not can_view_order(customer, {"owner_id": 6, "tenant_id": 1})
    assert safe_return_url("/account/orders", "shop.example")

def test_segmentation():
    customers = [Customer(1, "a@test.local", "north", 5000), Customer(2, "b@test.local", "south", 100)]
    assert len(segment(customers, 1000)) == 1

def test_retry_backoff():
    assert retry_delays(3) == [2, 4, 8]

def test_settlement_basic():
    assert sum_by_merchant([{"merchant_id": 1, "amount": 120}, {"merchant_id": 1, "amount": 80}]) == {1: 200}
    assert reconcile([{"reference":"r1","amount":10}], [{"reference":"r1","amount":10}]) == []


def test_follower_callbacks_keep_own_recipient():
    from orderflow.notifications import notify_followers
    callbacks = notify_followers(["a@test.local", "b@test.local"], "ORD-1")
    assert [callback()["recipient"] for callback in callbacks] == ["a@test.local", "b@test.local"]
