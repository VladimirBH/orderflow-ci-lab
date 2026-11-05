"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger("orderflow.audit")

# Substrings, so variants like "client_secret", "X-Api-Key" or "user_email" are caught too.
SENSITIVE_MARKERS = (
    "password",
    "passwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "email",
    "phone",
    "card",
)


def is_sensitive_key(key) -> bool:
    normalized = str(key).casefold().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_MARKERS)


def redact_sensitive(value):
    """Recursively replace values stored under sensitive keys, at any nesting depth."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if is_sensitive_key(key) else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    return value


def make_event(actor: str, action: str, attributes: dict) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "attributes": redact_sensitive(attributes),
    }


def serialize_event(event: dict) -> str:
    # Redact at the serialization boundary, so an event built elsewhere can't leak raw values.
    return json.dumps(redact_sensitive(event), ensure_ascii=False, sort_keys=True)


def record_operation(actor: str, action: str, attributes: dict) -> dict:
    event = make_event(actor, action, attributes)
    LOG.info("AUDIT_EVENT %s", serialize_event(event))
    return event


def summarize_events(events: list[dict]) -> dict:
    counts = {}
    for event in events:
        action = event["action"]
        counts[action] = counts.get(action, 0) + 1
    return counts
