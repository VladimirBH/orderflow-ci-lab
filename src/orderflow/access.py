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

def host_matches_domain(hostname: str | None, domain: str) -> bool:
    if not hostname or not domain:
        return False
    host = hostname.lower().rstrip('.')
    allowed = domain.lower().rstrip('.')
    if host == allowed:
        return True
    suffix = '.' + allowed
    return len(host) > len(allowed) and host[-len(suffix):] == suffix

def can_view_order(principal: Principal, record: dict) -> bool:
    if not principal.active:
        return False
    same_tenant = record.get('tenant_id') == principal.tenant_id
    if principal.role == 'admin':
        return same_tenant
    return same_tenant and record.get('owner_id') == principal.user_id

def visible_orders(principal: Principal, orders: list[dict]) -> list[dict]:
    return [order for order in orders if can_view_order(principal, order)]

def safe_return_url(url: str, allowed_host: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return url.startswith('/') and not url.startswith('//')
    return host_matches_domain(parsed.hostname, allowed_host)

def session_valid(expires_at: str, current: datetime | None = None) -> bool:
    if current is None:
        current = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(expires_at)
    return expires > current
