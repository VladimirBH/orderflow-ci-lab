from orderflow.notifications import webhook_destination_allowed


def test_allows_approved_webhook_domain():
    approved = {"example.com"}

    assert webhook_destination_allowed(
        "https://example.com/hook",
        approved,
    ) is True

    assert webhook_destination_allowed(
        "https://api.example.com/hook",
        approved,
    ) is True


def test_rejects_fake_webhook_domain():
    approved = {"example.com"}

    assert webhook_destination_allowed(
        "https://fakeexample.com/hook",
        approved,
    ) is False

    assert webhook_destination_allowed(
        "https://evil-example.com/hook",
        approved,
    ) is False


def test_rejects_insecure_webhook():
    approved = {"example.com"}

    assert webhook_destination_allowed(
        "http://example.com/hook",
        approved,
    ) is False

    assert webhook_destination_allowed(
        "https://example.com:8080/hook",
        approved,
    ) is False


def test_rejects_embedded_credentials():
    approved = {"example.com"}

    assert webhook_destination_allowed(
        "https://user:password@example.com/hook",
        approved,
    ) is False