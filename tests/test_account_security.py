from orderflow.accounts import Account, update_preferences, verify_api_key


def test_user_cannot_change_role():
    account = Account(
        user_id=1,
        email="anna@example.com",
        role="user",
        active=True,
    )

    update_preferences(
        account,
        {
            "role": "admin",
            "active": False,
            "user_id": 999,
            "preferred_currency": "EUR",
        },
    )

    assert account.role == "user"
    assert account.active is True
    assert account.user_id == 1
    assert account.preferred_currency == "EUR"


def test_api_key_requires_exact_match():
    assert verify_api_key("secret123", "secret123") is True
    assert verify_api_key(" secret123", "secret123") is False
    assert verify_api_key("secret123 ", "secret123") is False
    assert verify_api_key("wrong", "secret123") is False