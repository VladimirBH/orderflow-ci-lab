"""Outbound notification preparation and retry bookkeeping."""
import logging
from functools import partial
from urllib.parse import urlparse

from .hosts import host_matches

LOG = logging.getLogger('orderflow.notifications')

def webhook_destination_allowed(destination: str, approved_domains: set[str]) -> bool:
    parsed = urlparse(destination)
    return parsed.scheme == 'https' and any(
        host_matches(parsed.hostname, domain) for domain in approved_domains
    )

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
    return [partial(_follower_notification, follower, reference) for follower in followers]


def _follower_notification(recipient: str, reference: str) -> dict:
    return {'recipient': recipient, 'reference': reference}
