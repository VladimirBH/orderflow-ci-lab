"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger('orderflow.audit')

REDACTED = '***'
SENSITIVE_MARKERS = ('password', 'secret', 'token', 'api_key', 'apikey', 'authorization',
                     'card', 'cvv', 'email', 'phone', 'passport')


def _is_sensitive(key) -> bool:
    name = str(key).lower()
    return any(marker in name for marker in SENSITIVE_MARKERS)


def redact(value):
    """Return a copy of value with credentials and personal data masked."""
    if isinstance(value, dict):
        return {key: REDACTED if _is_sensitive(key) else redact(item)
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


def make_event(actor: str, action: str, attributes: dict):
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor, 'action': action, 'attributes': attributes}

def record_operation(actor: str, action: str, attributes: dict):
    event = make_event(actor, action, attributes)
    LOG.info('AUDIT_EVENT %s', json.dumps(redact(event)))
    return event

def summarize_events(events: list[dict]):
    counts = {}
    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1
    return counts
