"""Outbound notification preparation and retry bookkeeping."""
import logging
from urllib.parse import urlparse

LOG = logging.getLogger('orderflow.notifications')

def webhook_destination_allowed(
    destination: str,
    approved_domains: set[str],
) -> bool:
    try:
        parsed = urlparse(destination)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme != "https" or not hostname:
        return False

    if not parsed.netloc or parsed.username or parsed.password:
        return False

    if port not in (None, 443):
        return False

    hostname_parts = hostname.lower().rstrip(".").split(".")

    for domain in approved_domains:
        domain_parts = domain.lower().rstrip(".").split(".")

        if not all(domain_parts):
            continue

        if hostname_parts == domain_parts:
            return True

        if (
            len(hostname_parts) > len(domain_parts)
            and hostname_parts[-len(domain_parts):] == domain_parts
        ):
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
