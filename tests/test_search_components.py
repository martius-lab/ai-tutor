from aitutor.search.components import BADGE_STYLES
from aitutor.search.state import SearchKey


def test_every_search_key_has_a_badge_style():
    assert set(BADGE_STYLES) == set(SearchKey)
