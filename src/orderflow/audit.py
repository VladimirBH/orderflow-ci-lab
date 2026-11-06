"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger('orderflow.audit')

def make_event(actor: str, action: str, attributes: dict):
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor, 'action': action, 'attributes': attributes}

SENSITIVE_KEYS = {'password', 'token', 'secret', 'api_key', 'credit_card'}

def _redact(data: dict) -> dict:
    return {k: ('***' if k.lower() in SENSITIVE_KEYS else v) for k, v in data.items()}

def record_operation(actor: str, action: str, attributes: dict):
    event = make_event(actor, action, attributes)
    safe_event = {**event, 'attributes': _redact(event['attributes'])}
    LOG.info('AUDIT_EVENT %s', json.dumps(safe_event))
    return event

def summarize_events(events: list[dict]):
    counts = {}
    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1
    return counts
