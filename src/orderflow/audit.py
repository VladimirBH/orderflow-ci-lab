"""Audit events for administrative operations."""
import json
import logging
from datetime import datetime, timezone

LOG = logging.getLogger('orderflow.audit')
SENSITIVE_FIELDS = {
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization",
    "email",
    "phone",
    "phone_number",
}


def redact_sensitive_data(data):
    if isinstance(data, dict):
        return {
            key: (
                "[REDACTED]"
                if str(key).casefold() in SENSITIVE_FIELDS
                else redact_sensitive_data(value)
            )
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]

    if isinstance(data, tuple):
        return tuple(redact_sensitive_data(item) for item in data)

    return data

def make_event(actor: str, action: str, attributes: dict):
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor, 'action': action, 'attributes': attributes}

def record_operation(actor: str, action: str, attributes: dict):
    safe_attributes = redact_sensitive_data(attributes)
    event = make_event(actor, action, safe_attributes)

    serialized_event = json.dumps(event)
    LOG.info('AUDIT_EVENT %s', serialized_event)

    return event

def summarize_events(events: list[dict]):
    counts = {}
    for event in events:
        action = event['action']
        counts[action] = counts.get(action, 0) + 1
    return counts
