import logging

from orderflow.audit import record_operation


def test_audit_redacts_sensitive_data(caplog):
    attributes = {
        "order_id": 42,
        "password": "super-secret-password",
        "details": {
            "token": "secret-access-token",
            "status": "completed",
        },
    }

    with caplog.at_level(logging.INFO, logger="orderflow.audit"):
        event = record_operation(
            actor="admin",
            action="update_order",
            attributes=attributes,
        )

    assert event["attributes"]["password"] == "[REDACTED]"
    assert event["attributes"]["details"]["token"] == "[REDACTED]"

    assert event["attributes"]["order_id"] == 42
    assert event["attributes"]["details"]["status"] == "completed"

    assert "super-secret-password" not in caplog.text
    assert "secret-access-token" not in caplog.text
    assert "[REDACTED]" in caplog.text

    assert attributes["password"] == "super-secret-password"