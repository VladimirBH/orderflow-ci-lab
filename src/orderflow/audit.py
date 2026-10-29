"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger('orderflow.audit')

def redact(data):
    sensitive = {'password', 'token', 'secret', 'api_key', 'email'}

    if isinstance(data, dict):
        return {
            key: '[REDACTED]' if str(key).lower() in sensitive else redact(value)
            for key, value in data.items()
        }

    if isinstance(data, (list, tuple)):
        return [redact(value) for value in data]

    return data

def make_event(actor: str, action: str, attributes: dict):
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor, 'action': action, 'attributes': attributes}

def record_operation(actor: str, action: str, attributes: dict):
    event = make_event(actor, action, attributes)
    safe_event = redact(event)

    LOG.info('AUDIT_EVENT %s', json.JSONEncoder(ensure_ascii=False).encode(safe_event))
    return event

def summarize_events(events: list[dict]):
    counts = {}
    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1
    return counts
