"""Outbound notification preparation and retry bookkeeping."""
import logging
from urllib.parse import urlparse

LOG = logging.getLogger('orderflow.notifications')

def webhook_destination_allowed(destination: str, approved_domains: set[str]) -> bool:
    parsed = urlparse(destination)

    if parsed.scheme != 'https' or not parsed.hostname:
        return False

    host_parts = parsed.hostname.lower().rstrip('.').split('.')

    for domain in approved_domains:
        allowed = domain.lower().strip('.')
        if not allowed:
            continue

        domain_parts = allowed.split('.')
        if host_parts[-len(domain_parts):] == domain_parts:
            return True

    return False

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
        callbacks.append(lambda follower=follower: {'recipient': follower, 'reference': reference})
    return callbacks
