"""The parser for the search of tables"""

# working parser ("quote test" does not work)
from pyparsing import (
    Word,
    alphas,
    dblQuotedString,
    removeQuotes,
    oneOf,
    ParserElement,
)


def parse_query_keys(query: str, keys: list[str]) -> list[tuple[str, str]]:
    """
    Parses a query string to extract key-value pairs and remaining tokens.

    Args:
        query (str): The query string to parse.
        keys (list[str]): The list of keys to look for in the query.

    Returns:
        list[tuple[str, str]]: A list of tuples where each tuple contains a key and its
                               corresponding value.
    """
    ParserElement.setDefaultWhitespaceChars(" \t")

    key = oneOf(keys)
    quoted_value = dblQuotedString.setParseAction(removeQuotes)
    pair = (key + ":" + quoted_value).setParseAction(lambda t: (t[0], t[2]))

    word = Word(alphas + ":")

    token = pair | word.setParseAction(lambda t: ("rest", t[0]))

    result = []
    for t in token.searchString(query):
        result.append(t[0] if isinstance(t[0], tuple) else t)
    return result


def test():
    """Test the parse_query_keys function."""
    query = (
        "admin "
        'user:"test" '
        'tag:"test" '
        'exercise:"test" '
        'wrongkey:"test" '
        "tag:noquotes"
        '"quote test"'
    )
    keys = ["tag", "user", "exercise"]
    result = parse_query_keys(query, keys)
    print("Parsed query:", result)


if __name__ == "__main__":
    test()


# other version
# from pyparsing import (
#     Regex,
#     Word,
#     alphas,
#     dblQuotedString,
#     removeQuotes,
#     oneOf,
#     ParserElement,
# )


# def parse_query_keys(query: str, keys: list[str]) -> list[tuple[str, str]]:
#     """
#     Parses a query string to extract key-value pairs and remaining tokens.

#     Args:
#         query (str): The query string to parse.
#         keys (list[str]): The list of keys to look for in the query.

#     Returns:
#         list[tuple[str, str]]: A list of tuples where each tuple contains a key and its
#                                corresponding value.
#     """
#     # set default whitespace characters to space and tab
#     ParserElement.setDefaultWhitespaceChars(" \t")

#     # parse values like 'key:"value"'
#     key = oneOf(keys)
#     quoted_value = dblQuotedString.setParseAction(removeQuotes)
#     pair = (key + ":" + quoted_value).setParseAction(lambda t: (t[0], t[2]))

#     # parse values like "quoted value"
#     rest_quoted_value = dblQuotedString.setParseAction(
#         lambda t, loc, s: ("rest", removeQuotes(t, loc, s))
#     )

#     # parse everything else
#     rest_word = Regex(r"[^ \t]+").setParseAction(lambda t: ("rest", t[0]))

#     token = (
#         pair | rest_quoted_value | rest_word
#     )  # word.setParseAction(lambda t: ("rest", t[0]))

#     result = []
#     for t in token.searchString(query):
#         result.append(t[0] if isinstance(t[0], tuple) else t)
#     return result


# def test():
#     """Test the parse_query_keys function."""
#     query = (
#         "admin "
#         'user:"test" '
#         'tag:"test" '
#         'exercise:"test" '
#         'wrongkey:"test" '
#         "tag:noquotes "
#         '"quot etest"'
#     )
#     keys = ["tag", "user", "exercise"]
#     result = parse_query_keys(query, keys)
#     print("Parsed query:", result)


# if __name__ == "__main__":
#     test()
