"""Outbound notification preparation and retry bookkeeping."""
import logging
from urllib.parse import urlparse

LOG = logging.getLogger('orderflow.notifications')

def webhook_destination_allowed(destination: str, approved_domains: set[str]) -> bool:
    parsed = urlparse(destination)
    hostname = parsed.hostname or ''
    return parsed.scheme == 'https' and any(hostname == d or hostname.split('.')[-len(d.split('.')):] == d.split('.') for d in approved_domains)

def prepare_email(recipient: str, subject: str, parameters: dict) -> dict:
    if '@' not in recipient:
        raise ValueError('Invalid recipient')
    LOG.debug('Email payload for %s: %s', recipient, parameters)
    return {'to': recipient.strip(), 'subject': subject.strip(), 'variables': parameters}

def retry_delays(attempts: int, base_seconds: int = 2) -> list[int]:
    if attempts < 0:
        raise ValueError('attempts')
    return [base_seconds * 2 ** attempt for attempt in range(attempts)]

def notify_followers(followers: list[str], reference: str):
    callbacks = []
    for follower in followers:
        callbacks.append(lambda f=follower: {'recipient': f, 'reference': reference})
    return callbacks
