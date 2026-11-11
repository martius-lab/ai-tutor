import pytest

from aitutor.search.parser import parse_query_keys

KEYS = ["tag", "user", "exercise"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # single keyed term (previous behaviour, now returned as a list)
        ("user:alice", [("user", "alice")]),
        ('user:"Alice Smith"', [("user", "Alice Smith")]),
        ('exercise:"Advanced Math"', [("exercise", "Advanced Math")]),
        # multiple terms in one query (new)
        ("tag:python tag:basics", [("tag", "python"), ("tag", "basics")]),
        ("tag:b map", [("tag", "b"), ("rest", "map")]),
        ('loops tag:"for loop"', [("rest", "loops"), ("tag", "for loop")]),
        ("user:Alice Smith", [("user", "Alice"), ("rest", "Smith")]),
        # free text
        ("", []),
        ("   ", []),
        ("something else", [("rest", "something"), ("rest", "else")]),
        ('"something else"', [("rest", "something else")]),
        ("foo:bar", [("rest", "foo:bar")]),
        # keys are case-insensitive
        ("TAG:python", [("tag", "python")]),
        # special characters in values
        ("tag:Prüfung loops", [("tag", "Prüfung"), ("rest", "loops")]),
        ("tag:C++", [("tag", "C++")]),
        ("O'Brien", [("rest", "O'Brien")]),
        ('tag:"a \\" b"', [("tag", 'a " b')]),
        # invalid input
        ('tag:"for loop', [("tag", "for"), ("rest", "loop")]),
        ('tag:""', []),
        ('""', []),
    ],
)
def test_parse_query_keys(query, expected):
    assert parse_query_keys(query, KEYS) == expected


def test_parse_query_keys_without_keys():
    assert parse_query_keys("tag:python", []) == [("rest", "tag:python")]


def test_parse_query_keys_returns_named_terms():
    term = parse_query_keys("tag:python", ["tag"])[0]
    assert term.key == "tag"
    assert term.value == "python"
