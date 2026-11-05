"""Outbound notification preparation and retry bookkeeping."""
import logging
from urllib.parse import urlparse

LOG = logging.getLogger("orderflow.notifications")

def webhook_destination_allowed(destination: str, approved_hosts: set[str]) -> bool:
    # HTTP clients may split "\" or embedded credentials differently than urlparse.
    if "\\" in destination or not destination.isprintable():
        return False

    parsed = urlparse(destination)
    hostname = (parsed.hostname or "").rstrip(".")

    if parsed.scheme != "https" or not hostname or parsed.username is not None:
        return False

    # Exact host match only: subdomains of an approved host are not trusted.
    return hostname in {host.lower().rstrip(".") for host in approved_hosts}


def prepare_email(recipient: str, subject: str, parameters: dict) -> dict:
    if "@" not in recipient:
        raise ValueError("Invalid recipient")

    LOG.debug("Email payload prepared for recipient")
    return {
        "to": recipient.strip(),
        "subject": subject.strip(),
        "variables": parameters,
    }


def retry_delays(attempts: int, base_seconds: int = 2) -> list[int]:
    if attempts < 0:
        raise ValueError("attempts")
    if base_seconds < 0:
        raise ValueError("base_seconds")

    return [base_seconds * 2 ** attempt for attempt in range(attempts)]


def notify_followers(followers: list[str], reference: str) -> list:
    callbacks = []

    for follower in followers:
        callbacks.append(
            lambda follower=follower: {
                "recipient": follower,
                "reference": reference,
            }
        )

    return callbacks
