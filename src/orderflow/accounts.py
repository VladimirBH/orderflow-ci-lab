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

EDITABLE_PREFERENCES = frozenset({'preferred_currency'})


def update_preferences(account: Account, changes: dict):
    forbidden = set(changes) - EDITABLE_PREFERENCES
    if forbidden:
        raise PermissionError('Fields are not editable: ' + ', '.join(sorted(forbidden)))
    for field_name in EDITABLE_PREFERENCES.intersection(changes):
        setattr(account, field_name, changes[field_name])
    return account_view(account)

def verify_webhook(payload: bytes, signature: str, secret: str):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_api_key(candidate: str, configured: str) -> bool:
    if not candidate or not configured:
        return False
    return hmac.compare_digest(candidate.encode('utf-8'), configured.encode('utf-8'))
