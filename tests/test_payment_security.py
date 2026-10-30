import hashlib
import hmac
import json

from orderflow.billing import Payment, accept_payment_callback


SECRET = "payment-secret"


def signed_payload(data: dict) -> tuple[bytes, str]:
    payload = json.dumps(data).encode("utf-8")
    signature = hmac.new(
        SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return payload, signature


def test_valid_payment_callback():
    payment = Payment(42, 1500, "RUB", "PAY-42", "captured")

    payload, signature = signed_payload({
        "order_id": 42,
        "amount": 1500,
        "currency": "RUB",
        "reference": "PAY-42",
        "status": "captured",
    })

    assert accept_payment_callback(
        payment, "RUB", {42}, payload, signature, SECRET
    ) is True


def test_rejects_forged_payment_callback():
    payment = Payment(42, 1500, "RUB", "PAY-42", "captured")

    payload, _ = signed_payload({
        "order_id": 42,
        "amount": 1500,
        "currency": "RUB",
        "reference": "PAY-42",
        "status": "captured",
    })

    assert accept_payment_callback(
        payment, "RUB", {42}, payload, "invalid-signature", SECRET
    ) is False


def test_rejects_payment_data_not_matching_signed_payload():
    payment = Payment(42, 1500, "RUB", "PAY-42", "captured")

    payload, signature = signed_payload({
        "order_id": 42,
        "amount": 100,
        "currency": "RUB",
        "reference": "PAY-42",
        "status": "captured",
    })

    assert accept_payment_callback(
        payment, "RUB", {42}, payload, signature, SECRET
    ) is False