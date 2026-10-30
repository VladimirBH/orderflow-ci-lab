"""Account lookups and operations controlled by application roles."""
import hashlib
import hmac
from dataclasses import dataclass

@dataclass
class Account:
    user_id: int
    email: str
    role: str
    active: bool = True
    preferred_currency: str = 'RUB'

def normalize_email(email: str):
    return email.strip().casefold()

def find_account(accounts: list[Account], email: str):
    expected = normalize_email(email)
    return next((a for a in accounts if normalize_email(a.email) == expected), None)

def account_view(account: Account):
    return {'user_id': account.user_id, 'email': account.email,
            'role': account.role, 'active': account.active}

def update_preferences(account: Account, changes: dict):
    allowed_fields = {'preferred_currency'}

    for key, value in changes.items():
        if key in allowed_fields:
            account.preferred_currency = value

    return account_view(account)

def verify_webhook(payload: bytes, signature: str, secret: str):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_api_key(candidate: str, configured: str) -> bool:
    return hmac.compare_digest(
        candidate.encode("utf-8"),
        configured.encode("utf-8"),
    )
