
"""Access checks for shared order resources and session tokens."""

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse


@dataclass(frozen=True)
class Principal:
    user_id: int
    role: str
    tenant_id: int
    active: bool = True


def can_view_order(principal: Principal, record: dict) -> bool:
    same_tenant = record.get("tenant_id") == principal.tenant_id
    if not principal.active or not same_tenant:
        return False
    # The admin role only widens access within the principal's own tenant.
    return principal.role == "admin" or record.get("owner_id") == principal.user_id


def visible_orders(principal: Principal, orders: list[dict]) -> list[dict]:
    return [
        order
        for order in orders
        if can_view_order(principal, order)
    ]


def safe_return_url(url: str, allowed_host: str) -> bool:
    # Browsers read "\" as "/" and drop tabs/newlines, so "/\evil.example" leaves the site.
    if "\\" in url or not url.isprintable():
        return False
    parsed = urlparse(url)
    if not parsed.netloc:
        return url.startswith("/") and not url.startswith("//")
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        return False
    # Exact host match only: any subdomain is a different, possibly untrusted, origin.
    return parsed.hostname.rstrip(".") == allowed_host.lower().rstrip(".")


def session_valid(expires_at: str, current: datetime | None = None) -> bool:
    if current is None:
        current = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(expires_at)
    if expires.tzinfo is None:
        return False
    return expires > current
