
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
    preferred_currency: str = "RUB"


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def find_account(accounts: list[Account], email: str) -> Account | None:
    expected = normalize_email(email)
    return next((account for account in accounts if normalize_email(account.email) == expected), None)


def account_view(account: Account) -> dict:
    return {
        "user_id": account.user_id,
        "email": account.email,
        "role": account.role,
        "active": account.active,
    }


def update_preferences(account: Account, changes: dict) -> dict:
    # Each editable preference is assigned explicitly; role, active and other
    # account attributes can never be reached through user-supplied keys.
    if "preferred_currency" in changes:
        currency = changes["preferred_currency"]
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
            raise ValueError("Invalid currency code")
        account.preferred_currency = currency.upper()
    return account_view(account)


def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    # Compare bytes: compare_digest raises TypeError on non-ASCII str input.
    return hmac.compare_digest(expected.encode(), signature.encode())


def verify_api_key(candidate: str, configured: str) -> bool:
    return hmac.compare_digest(candidate.strip(), configured.strip())
