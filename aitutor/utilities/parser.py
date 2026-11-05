"""The parser for the search engine"""

from pyparsing import (
    ParseException,
    ParseResults,
    QuotedString,
    Regex,
    ZeroOrMore,
    one_of,
)

# A single search term as (key, value), e.g. ("tag", "for loop").
SearchTerm = tuple[str, str]

# Key assigned to terms without a recognized `key:` prefix.
FREE_TEXT_KEY = "rest"

# Double-quoted value; quotes are stripped and `\"` escapes a literal quote.
QUOTED_VALUE = QuotedString('"', esc_char="\\")

# Unquoted value; runs until the next whitespace or double quote.
BARE_VALUE = Regex(r'[^\s"]+')

VALUE = QUOTED_VALUE | BARE_VALUE


def _to_keyed_term(tokens: ParseResults) -> SearchTerm:
    """Convert `['TAG', ':', 'python']` to `('tag', 'python')`."""
    return str(tokens[0]).lower(), str(tokens[2])


def _to_free_term(tokens: ParseResults) -> SearchTerm:
    """Convert `['loops']` to `('rest', 'loops')`."""
    return FREE_TEXT_KEY, str(tokens[0])


# A value without a key, matched against all searchable columns.
FREE_TERM = VALUE.copy().set_parse_action(_to_free_term)


def parse_query_keys(query: str, keys: list[str]) -> list[SearchTerm]:
    """
    Split a search query into (key, value) terms.

    example: parse_query_keys('loops tag:"for loop" foo:bar', ["tag"])
    [('rest', 'loops'), ('tag', 'for loop'), ('rest', 'foo:bar')]

    Keys are case-insensitive. Unknown keys and words without a key are free
    text. Empty values are dropped and unbalanced quotes are ignored.
    """
    key = one_of(keys, caseless=True)
    keyed_term = (key + ":" + VALUE).set_parse_action(_to_keyed_term)
    grammar = ZeroOrMore(keyed_term | FREE_TERM)

    try:
        terms = grammar.parse_string(query, parse_all=True)
    except ParseException:
        terms = grammar.parse_string(query.replace('"', ""), parse_all=True)

    return [(k, v) for k, v in terms if v.strip()]
