
from orderflow.access import (
    Principal,
    can_view_order,
    visible_orders,
    safe_return_url,
    session_valid,
)
from datetime import datetime, timedelta, timezone


def test_admin_cannot_access_other_tenant():
    admin = Principal(user_id=1, role="admin", tenant_id=10)
    order = {"owner_id": 2, "tenant_id": 20}

    assert can_view_order(admin, order) is False


def test_admin_can_access_own_tenant():
    admin = Principal(user_id=1, role="admin", tenant_id=10)
    order = {"owner_id": 2, "tenant_id": 10}

    assert can_view_order(admin, order) is True


def test_inactive_user_cannot_access_order():
    user = Principal(user_id=1, role="user", tenant_id=10, active=False)
    order = {"owner_id": 1, "tenant_id": 10}

    assert can_view_order(user, order) is False


def test_user_can_access_own_order():
    user = Principal(user_id=1, role="user", tenant_id=10)
    order = {"owner_id": 1, "tenant_id": 10}

    assert can_view_order(user, order) is True


def test_user_cannot_access_another_users_order():
    user = Principal(user_id=1, role="user", tenant_id=10)
    order = {"owner_id": 2, "tenant_id": 10}

    assert can_view_order(user, order) is False


def test_visible_orders_filters_other_tenants():
    user = Principal(user_id=1, role="admin", tenant_id=10)

    orders = [
        {"owner_id": 1, "tenant_id": 10},
        {"owner_id": 2, "tenant_id": 10},
        {"owner_id": 3, "tenant_id": 20},
    ]

    result = visible_orders(user, orders)

    assert len(result) == 2
    assert all(order["tenant_id"] == 10 for order in result)


def test_safe_return_url_allows_approved_domain():
    assert safe_return_url(
        "https://shop.example.com/orders", "example.com"
    ) is True


def test_safe_return_url_rejects_fake_domain():
    assert safe_return_url(
        "https://fakeexample.com/orders", "example.com"
    ) is False


def test_session_valid_accepts_future_expiration():
    now = datetime.now(timezone.utc)
    future = (now + timedelta(hours=1)).isoformat()

    assert session_valid(future, now) is True


def test_session_valid_rejects_expired_session():
    now = datetime.now(timezone.utc)
    past = (now - timedelta(hours=1)).isoformat()

    assert session_valid(past, now) is False
