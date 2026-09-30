"""The parser for the search of tables"""

from pyparsing import (
    ParserElement,
    Word,
    alphanums,
    dbl_quoted_string,
    one_of,
    remove_quotes,
)


def parse_query_keys(query: str, keys: list[str]) -> tuple[str, str]:
    """
    Parses a query string and returns a single (key, value) tuple.

    If Input matches the pattern:
        'key:value' or 'key:"value with spaces"',
    it returns ('key', 'value') or ('key', 'value with spaces').

    Else it returns ('rest', query).
    """
    ParserElement.set_default_whitespace_chars(" \t")

    key = one_of(keys)
    quoted_value = dbl_quoted_string.set_parse_action(remove_quotes)
    unquoted_value = Word(alphanums + "_-./")
    value = quoted_value | unquoted_value

    pair = (key + ":" + value).set_parse_action(lambda t: (t[0], t[2]))

    try:
        result = pair.parse_string(query, parse_all=True)[0]
        return (str(result[0]), str(result[1]))
    except Exception:
        return ("rest", query)
