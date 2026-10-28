"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger('orderflow.audit')
_SENSITIVE_PARTS = ('password', 'token', 'secret', 'email', 'credential', 'authorization')

def redact_attributes(attributes: dict) -> dict:
    cleaned = {}
    for key, value in attributes.items():
        lowered = str(key).lower()
        cleaned[key] = '***' if any(part in lowered for part in _SENSITIVE_PARTS) else value
    return cleaned

def make_event(actor: str, action: str, attributes: dict):
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor, 'action': action, 'attributes': attributes}

def record_operation(actor: str, action: str, attributes: dict):
    event = make_event(actor, action, redact_attributes(attributes))
    LOG.info('AUDIT_EVENT %s', json.dumps(event))
    return event

def summarize_events(events: list[dict]):
    counts = {}
    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1
    return counts
