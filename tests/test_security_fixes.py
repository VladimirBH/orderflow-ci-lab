from orderflow.access import safe_return_url
from orderflow.notifications import webhook_destination_allowed


def test_return_url_requires_exact_host():
    assert safe_return_url("https://shop.example/orders", "shop.example")
    assert not safe_return_url("https://evilshop.example/orders", "shop.example")
    assert not safe_return_url("https://shop.example.attacker.test/", "shop.example")
    assert not safe_return_url("//evil.test/path", "shop.example")


def test_webhook_domain_boundary():
    approved = {"partner.example"}
    assert webhook_destination_allowed("https://partner.example/hook", approved)
    assert webhook_destination_allowed("https://api.partner.example/hook", approved)
    assert not webhook_destination_allowed("https://evilpartner.example/hook", approved)
    assert not webhook_destination_allowed("http://partner.example/hook", approved)


def test_admin_cannot_cross_tenant_boundary():
    from orderflow.access import Principal, can_view_order, visible_orders
    admin = Principal(1, "admin", tenant_id=1)
    own_tenant = {"owner_id": 5, "tenant_id": 1}
    other_tenant = {"owner_id": 5, "tenant_id": 2}
    assert can_view_order(admin, own_tenant)
    assert not can_view_order(admin, other_tenant)
    assert visible_orders(admin, [own_tenant, other_tenant]) == [own_tenant]


def test_owner_cannot_read_record_of_other_tenant():
    from orderflow.access import Principal, can_view_order
    user = Principal(4, "user", tenant_id=1)
    assert not can_view_order(user, {"owner_id": 4, "tenant_id": 2})


def test_preferences_cannot_change_role_or_status():
    import pytest
    from orderflow.accounts import Account, update_preferences
    account = Account(7, "user@example.test", "user")
    with pytest.raises(PermissionError):
        update_preferences(account, {"role": "admin", "active": True})
    assert account.role == "user"
    update_preferences(account, {"preferred_currency": "EUR"})
    assert account.preferred_currency == "EUR"


def test_api_key_comparison_is_exact():
    from orderflow.accounts import verify_api_key
    assert verify_api_key("k-123", "k-123")
    assert not verify_api_key(" k-123 ", "k-123")
    assert not verify_api_key("", "")
    assert not verify_api_key("k-124", "k-123")


def test_audit_log_redacts_sensitive_fields(caplog):
    import logging
    from orderflow.audit import record_operation
    with caplog.at_level(logging.INFO, logger="orderflow.audit"):
        event = record_operation("admin", "user.update",
                                 {"user_id": 7, "password": "p@ss", "api_token": "t-1",
                                  "contact": {"email": "a@test.local"}})
    logged = caplog.text
    assert "p@ss" not in logged and "t-1" not in logged and "a@test.local" not in logged
    assert '"user_id": 7' in logged
    assert event["attributes"]["password"] == "p@ss"


def _request(handler_cls, path):
    import io
    handler = handler_cls.__new__(handler_cls)
    handler.path = path
    handler.request_version = "HTTP/1.1"
    handler.requestline = "GET " + path + " HTTP/1.1"
    handler.command = "GET"
    handler.wfile = io.BytesIO()
    handler.log_message = lambda *args: None
    handler.do_GET()
    return handler.wfile.getvalue().decode("utf-8")


def test_response_has_no_implementation_banner():
    import json
    from orderflow.web import Handler
    raw = _request(Handler, "/health")
    headers, body = raw.split("\r\n\r\n", 1)
    assert "X-Powered-By" not in headers
    assert json.loads(body) == {"status": "ok"}


def test_read_document_stays_inside_root(tmp_path):
    import pytest
    from orderflow.imports import read_document
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.txt").write_text("ok", encoding="utf-8")
    (tmp_path.parent / "outside.txt").write_text("secret", encoding="utf-8")
    assert read_document(str(tmp_path), "docs", "a.txt") == "ok"
    with pytest.raises(PermissionError):
        read_document(str(tmp_path), "docs", "../../outside.txt")


def _signed(payload, secret="s3cret"):
    import hashlib
    import hmac
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_payment_callback_requires_valid_signature():
    from orderflow.billing import Payment, accept_payment_callback
    payment = Payment(10, 1500, "rub", "ref-1", "captured")
    payload = b'{"order_id": 10}'
    assert accept_payment_callback(payment, "RUB", {10}, payload=payload,
                                   signature=_signed(payload), secret="s3cret")
    assert not accept_payment_callback(payment, "RUB", {10}, payload=payload,
                                       signature="forged", secret="s3cret")
    assert not accept_payment_callback(payment, "RUB", {11}, payload=payload,
                                       signature=_signed(payload), secret="s3cret")
    failed = Payment(10, 1500, "RUB", "ref-1", "failed")
    assert not accept_payment_callback(failed, "RUB", {10}, payload=payload,
                                       signature=_signed(payload), secret="s3cret")


def test_order_search_treats_email_as_data():
    from orderflow.storage import connect_database, find_orders_by_email, save_order
    with connect_database() as conn:
        save_order(conn, "a@test.local", 100)
        save_order(conn, "b@test.local", 200)
        assert find_orders_by_email(conn, "x' OR '1'='1") == []
        assert len(find_orders_by_email(conn, "a@test.local")) == 1


def test_quote_rejects_malformed_json():
    import io
    import json
    from orderflow.web import Handler
    body = b"{not json"
    handler = Handler.__new__(Handler)
    handler.path = "/api/quote"
    handler.request_version = "HTTP/1.1"
    handler.requestline = "POST /api/quote HTTP/1.1"
    handler.command = "POST"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler.log_message = lambda *args: None
    handler.do_POST()
    raw = handler.wfile.getvalue().decode("utf-8")
    assert raw.split("\r\n", 1)[0].split()[1] == "400"
    assert json.loads(raw.split("\r\n\r\n", 1)[1]) == {"error": "Invalid input"}


def test_unknown_resource_returns_404():
    import json
    from orderflow.web import Handler
    raw = _request(Handler, "/nope")
    assert raw.split("\r\n", 1)[0].split()[1] == "404"
    assert json.loads(raw.split("\r\n\r\n", 1)[1]) == {"error": "Unknown resource"}
