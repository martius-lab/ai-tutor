"""The parser for the search of tables"""

from pyparsing import (
    Word,
    alphanums,
    dblQuotedString,
    removeQuotes,
    oneOf,
    ParserElement,
)


def parse_query_keys(query: str, keys: list[str]) -> tuple[str, str]:
    """
    Parses a query string and returns a single (key, value) tuple.

    If Input matches the pattern:
        'key:value' or 'key:"value with spaces"',
    it returns ('key', 'value') or ('key', 'value with spaces').

    Else it returns ('rest', query).
    """
    ParserElement.setDefaultWhitespaceChars(" \t")

    key = oneOf(keys)
    quoted_value = dblQuotedString.setParseAction(removeQuotes)
    unquoted_value = Word(alphanums + "_-./")
    value = quoted_value | unquoted_value

    pair = (key + ":" + value).setParseAction(lambda t: (t[0], t[2]))

    try:
        result = pair.parseString(query, parseAll=True)[0]
        return (str(result[0]), str(result[1]))
    except Exception:
        return ("rest", query)


def test():
    """Test the parse_query_keys function."""
    queries = [
        "user:alice",
        'user:"Alice Smith"',
        "tag:science",
        'exercise:"Advanced Math"',
        "something else",
        "user:Alice Smith",
    ]
    keys = ["tag", "user", "exercise"]
    for q in queries:
        print(f"Input: {q}\nParsed: {parse_query_keys(q, keys)}\n")


if __name__ == "__main__":
    test()
