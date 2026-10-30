from orderflow.web import sanitize_response


def test_response_redacts_sensitive_fields():
    data = {
        "order_id": 42,
        "password": "super-secret",
        "details": {
            "api_key": "private-key",
            "status": "completed",
        },
        "items": [
            {"token": "secret-token", "quantity": 2}
        ],
    }

    result = sanitize_response(data)

    assert result["password"] == "[REDACTED]"
    assert result["details"]["api_key"] == "[REDACTED]"
    assert result["items"][0]["token"] == "[REDACTED]"

    assert result["order_id"] == 42
    assert result["details"]["status"] == "completed"
    assert result["items"][0]["quantity"] == 2


def test_response_does_not_modify_original_data():
    data = {
        "password": "original-password",
        "order_id": 15,
    }

    result = sanitize_response(data)

    assert result["password"] == "[REDACTED]"
    assert data["password"] == "original-password"
    assert result["order_id"] == 15