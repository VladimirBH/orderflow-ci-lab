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
    if not principal.active:
        return False
    if record.get('tenant_id') != principal.tenant_id:
        return False
    if principal.role == 'admin':
        return record.get('tenant_id') == principal.tenant_id
    return record.get('owner_id') == principal.user_id

def visible_orders(principal: Principal, orders: list[dict]) -> list[dict]:
    return [order for order in orders if can_view_order(principal, order)]

def safe_return_url(url: str, allowed_host: str) -> bool:
    parsed = urlparse(url)

    if not parsed.netloc:
        return url.startswith('/') and not url.startswith('//')

    hostname = (parsed.hostname or '').lower().rstrip('.')
    allowed = allowed_host.lower().rstrip('.')

    if not hostname or not allowed:
        return False

    return (parsed.scheme == 'https' and hostname.split('.')[-len(allowed.split('.')):] == allowed.split('.'))

def session_valid(expires_at: str, current: datetime | None = None) -> bool:
    if current is None:
        current = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(expires_at)
    return expires > current
