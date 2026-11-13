"""Search keys (e.g. `tag:python`) and the look of their badges."""

from typing import NamedTuple

from reflex_components_radix.themes.base import LiteralAccentColor

from aitutor.search.parser import FREE_TEXT_KEY


class SearchKey(NamedTuple):
    """A search key (`tag:python`) and the look of its badge."""

    key: str
    icon: str
    color: LiteralAccentColor


# search keys with the look (icon + color) of their badge
FREE_TEXT = SearchKey(FREE_TEXT_KEY, "search", "gray")  # also used for unknown keys
TAG = SearchKey("tag", "tag", "indigo")
USER = SearchKey("user", "user-round", "cyan")
EXERCISE = SearchKey("exercise", "book", "violet")
TITLE = SearchKey("title", "book", "violet")
DESCRIPTION = SearchKey("description", "book-open-text", "violet")

SEARCH_KEYS = [FREE_TEXT, TAG, USER, EXERCISE, TITLE, DESCRIPTION]
