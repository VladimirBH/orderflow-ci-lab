import hashlib
import hmac
from pathlib import Path

import pytest

from orderflow.access import Principal, can_view_order, safe_return_url
from orderflow.accounts import Account, update_preferences, verify_api_key
from orderflow.audit import record_operation
from orderflow.billing import Payment, accept_payment_callback
from orderflow.imports import read_document
from orderflow.notifications import notify_followers, webhook_destination_allowed


def test_admin_cannot_cross_tenant():
    admin = Principal(1, "admin", 1)
    assert can_view_order(admin, {"owner_id": 9, "tenant_id": 1})
    assert not can_view_order(admin, {"owner_id": 9, "tenant_id": 2})


def test_return_url_rejects_lookalike_host():
    assert safe_return_url("https://shop.example/orders", "shop.example")
    assert safe_return_url("https://a.shop.example/orders", "shop.example")
    assert not safe_return_url("https://evil-shop.example/orders", "shop.example")


def test_preferences_do_not_change_role():
    account = Account(1, "user@example.test", "user")
    view = update_preferences(account, {"role": "admin", "preferred_currency": "USD"})
    assert account.role == "user"
    assert account.preferred_currency == "USD"
    assert view["role"] == "user"


def test_api_key_keeps_surrounding_space():
    assert verify_api_key("secret", "secret")
    assert not verify_api_key(" secret", "secret")


def test_audit_redacts_password():
    event = record_operation("admin", "update", {"password": "hidden", "order_id": 5})
    assert event["attributes"]["password"] == "***"
    assert event["attributes"]["order_id"] == 5


def test_payment_callback_requires_signature():
    payment = Payment(1, 500, "RUB", "ref-1", "captured")
    assert not accept_payment_callback(payment, "RUB", {1})
    secret = "top-secret"
    payload = b"1:500:ref-1"
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert accept_payment_callback(payment, "RUB", {1}, signature, secret)


def test_document_cannot_escape_storage(tmp_path: Path):
    root = tmp_path / "storage"
    folder = root / "notes"
    folder.mkdir(parents=True)
    (folder / "note.txt").write_text("ok", encoding="utf-8")
    assert read_document(str(root), "notes", "note.txt") == "ok"
    with pytest.raises(ValueError):
        read_document(str(root), "..", "outside.txt")


def test_followers_keep_own_addresses():
    callbacks = notify_followers(["a@test.local", "b@test.local"], "ORD-1")
    assert [callback()["recipient"] for callback in callbacks] == ["a@test.local", "b@test.local"]


def test_webhook_rejects_lookalike_domain():
    assert webhook_destination_allowed("https://shop.example/hook", {"shop.example"})
    assert not webhook_destination_allowed("https://evil-shop.example/hook", {"shop.example"})
