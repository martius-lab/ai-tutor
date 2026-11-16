"""Helpers for restricting registration to certain email domains."""

import re

#: Hostname syntax per RFC 1035/1123, e.g. "example.com".  It is checked on the
#: ASCII form from `_to_ascii`, so internationalized domains like "tübingen.de"
#: (punycode "xn--tbingen-n2a.de") are accepted as well:
#: - dot-separated labels of lower-case letters, digits and hyphens,
_DOMAIN_RE = re.compile(
    r"(?=.{1,253}\Z)"  # total length
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"  # labels, each followed by a dot
    r"(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})"  # top-level domain
)


def _to_ascii(domain: str) -> str:
    """Convert a domain to lower-case ASCII, e.g. "Tübingen.de" -> "xn--tbingen-n2a.de".

    If the domain cannot be converted (e.g. empty or overlong labels), it is
    returned unchanged; `_DOMAIN_RE` rejects it then anyway.
    """
    domain = domain.lower()
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return domain


def parse_email_domains(value: str) -> list[str]:
    """Split the comma-separated list of allowed domains from the config.

    Args:
        value: The comma-separated list, e.g. "uni-tuebingen.de, example.com".

    Returns:
        The lower-case domains without empty entries and duplicates.  Empty if no
        restriction is configured.
    """
    domains = (item.strip().lower() for item in value.split(","))
    return list(dict.fromkeys(domain for domain in domains if domain))


def find_invalid_email_domains(value: str) -> list[str]:
    """Return the entries of the comma-separated list that are not valid domains."""
    return [
        domain
        for domain in parse_email_domains(value)
        if not _DOMAIN_RE.fullmatch(_to_ascii(domain))
    ]


def is_email_domain_allowed(email: str, allowed_domains: list[str]) -> bool:
    """Check whether an email address belongs to one of the allowed domains.

    Subdomains are included, i.e. if "example.com" is allowed, "foo@bar.example.com"
    is accepted as well, but "foo@barexample.com" is not.

    Args:
        email: The email address to check.
        allowed_domains: Domains as returned by `parse_email_domains`.  If empty,
            every address is allowed.

    Returns:
        True if the address may be used for registration.
    """
    if not allowed_domains:
        return True
    domain = _to_ascii(email.rpartition("@")[2])
    allowed = tuple(_to_ascii(domain) for domain in allowed_domains)
    return domain in allowed or domain.endswith(
        tuple("." + domain for domain in allowed)
    )
