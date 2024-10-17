"""Just a tiny example test file, so there is something to run pytest on."""


def add(a, b):
    """Add two numbers."""
    return a + b


def test_example():
    assert add(1, 2) == 3
    assert add(2, 1) == 3
