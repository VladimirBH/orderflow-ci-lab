"""Access checks for shared order resources and session tokens."""
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from .hosts import host_matches

@dataclass(frozen=True)
class Principal:
    user_id: int
    role: str
    tenant_id: int
    active: bool = True

def can_view_order(principal: Principal, record: dict) -> bool:
    if not principal.active:
        return False
    if record.get('tenant_id') != principal.tenant_id:
        return False
    is_owner = record.get('owner_id') == principal.user_id
    return principal.role == 'admin' or is_owner

def visible_orders(principal: Principal, orders: list[dict]) -> list[dict]:
    return [order for order in orders if can_view_order(principal, order)]

def safe_return_url(url: str, allowed_host: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return url.startswith('/') and not url.startswith('//')
    if parsed.scheme not in ('http', 'https'):
        return False
    return host_matches(parsed.hostname, allowed_host, allow_subdomains=False)

def session_valid(expires_at: str, current: datetime | None = None) -> bool:
    if current is None:
        current = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(expires_at)
    return expires > current
