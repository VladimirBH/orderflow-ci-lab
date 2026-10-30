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

    is_admin = principal.role == 'admin'
    is_owner = record.get('owner_id') == principal.user_id

    return is_admin or is_owner

def visible_orders(principal: Principal, orders: list[dict]) -> list[dict]:
    return [order for order in orders if can_view_order(principal, order)]

def safe_return_url(url: str, allowed_host: str) -> bool:
    parsed = urlparse(url)

    if not parsed.netloc:
        return url.startswith('/') and not url.startswith('//')

    hostname = parsed.hostname

    if hostname is None:
        return False

    hostname = hostname.lower().rstrip('.')
    allowed_host = allowed_host.lower().rstrip('.')

    if not allowed_host:
        return False

    if parsed.scheme != 'https':
        return False

    host_parts = hostname.split('.')
    allowed_parts = allowed_host.split('.')

    return (
        host_parts == allowed_parts
        or (
            len(host_parts) > len(allowed_parts)
            and host_parts[-len(allowed_parts):] == allowed_parts
        )
    )

def session_valid(expires_at: str, current: datetime | None = None) -> bool:
    if current is None:
        current = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(expires_at)
    return expires > current
