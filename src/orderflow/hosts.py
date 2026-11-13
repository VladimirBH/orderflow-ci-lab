"""Hostname comparison helpers that respect DNS label boundaries."""


def _labels(host: str) -> list[str]:
    return host.strip().rstrip('.').lower().split('.')


def host_matches(hostname: str | None, domain: str, allow_subdomains: bool = True) -> bool:
    """Return True if hostname equals domain or (optionally) is its subdomain.

    Comparison is performed by whole DNS labels, so ``evilshop.example`` does not
    match ``shop.example``.
    """
    if not hostname or not domain:
        return False
    host_labels = _labels(hostname)
    domain_labels = _labels(domain)
    if host_labels == domain_labels:
        return True
    if not allow_subdomains or len(host_labels) <= len(domain_labels):
        return False
    return host_labels[-len(domain_labels):] == domain_labels
