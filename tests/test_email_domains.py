import pytest

from aitutor.utilities.email_domains import (
    find_invalid_email_domains,
    is_email_domain_allowed,
    parse_email_domains,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", []),
        (" , ,", []),
        ("example.com", ["example.com"]),
        (" Uni-Tuebingen.de , example.com,", ["uni-tuebingen.de", "example.com"]),
        ("example.com, Example.com, example.com", ["example.com"]),
    ],
)
def test_parse_email_domains(value, expected):
    assert parse_email_domains(value) == expected


@pytest.mark.parametrize(
    "domain",
    [
        "uni-tuebingen.de",
        "CS.Example.com",
        "a-b.c.de",
        "3com.com",  # labels may start with a digit (RFC 1123)
        "xn--mnchen-3ya.de",  # punycode label
        "example.xn--p1ai",  # punycode TLD
        "a" * 63 + ".de",  # longest allowed label
        "tübingen.de",  # internationalized domain (IDN)
        "TÜBINGEN.de",
    ],
)
def test_valid_domains_are_accepted(domain):
    assert find_invalid_email_domains(domain) == []


@pytest.mark.parametrize(
    "domain",
    [
        "@uni.de",
        ".uni.de",
        "uni.de.",
        "uni..de",
        "uni de.com",
        "de",
        "tü bingen.de",  # whitespace in an internationalized domain
        "ü" * 60 + ".de",  # label longer than 63 characters after punycode
        "-uni.de",  # label starts with a hyphen
        "uni-.de",  # label ends with a hyphen
        "1.2.3.4",  # numeric TLD / IP address
        "uni.d",  # TLD too short
        "a" * 64 + ".de",  # label longer than 63 characters
        ("a" * 62 + ".") * 4 + "de",  # 254 characters in total
    ],
)
def test_invalid_domains_are_reported(domain):
    assert find_invalid_email_domains(f"example.com, {domain}") == [domain]


def test_no_restriction_allows_every_address():
    assert is_email_domain_allowed("foo@anything.org", [])


@pytest.mark.parametrize(
    "email",
    [
        "foo@example.com",
        "foo@bar.example.com",
        "jhnzaijnza@xokmx.co.example.com",
        "Foo@BAR.Example.COM",
    ],
)
def test_domain_and_subdomains_are_allowed(email):
    assert is_email_domain_allowed(email, ["example.com"])


@pytest.mark.parametrize(
    "email",
    [
        "foo@barexample.com",
        "foo@example.com.evil.org",
        "foo@example.org",
        "example.com@evil.org",
    ],
)
def test_other_domains_are_not_allowed(email):
    assert not is_email_domain_allowed(email, ["example.com"])


def test_any_of_multiple_domains_is_allowed():
    domains = ["uni-tuebingen.de", "example.com"]
    assert is_email_domain_allowed("a@uni-tuebingen.de", domains)
    assert is_email_domain_allowed("a@cs.example.com", domains)
    assert not is_email_domain_allowed("a@gmail.com", domains)


@pytest.mark.parametrize(
    ("email", "allowed"),
    [
        ("foo@tübingen.de", "tübingen.de"),
        ("foo@xn--tbingen-n2a.de", "tübingen.de"),
        ("foo@tübingen.de", "xn--tbingen-n2a.de"),
        ("foo@cs.TÜBINGEN.de", "tübingen.de"),  # subdomain + upper case
    ],
)
def test_unicode_and_punycode_domains_match(email, allowed):
    assert is_email_domain_allowed(email, [allowed])


def test_unicode_domain_does_not_match_lookalike():
    assert not is_email_domain_allowed("foo@bartübingen.de", ["tübingen.de"])
    assert not is_email_domain_allowed("foo@tubingen.de", ["tübingen.de"])
