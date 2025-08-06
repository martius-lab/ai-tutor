from aitutor.utilities.parser import parse_query_keys


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
    expected = [
        ("user", "alice"),
        ("user", "Alice Smith"),
        ("tag", "science"),
        ("exercise", "Advanced Math"),
        ("rest", "something else"),
        ("rest", "user:Alice Smith"),
    ]
    for query, exp in zip(queries, expected, strict=True):
        assert parse_query_keys(query, keys) == exp, f"Failed for query: {query}"
