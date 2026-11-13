"""Search state shared by all searchable pages."""

import contextlib
from abc import abstractmethod
from enum import StrEnum
from typing import Any

import reflex as rx

from aitutor.search.parser import FREE_TEXT_KEY, SearchTerm, parse_query_keys

#: maximum length of a search query typed by the user
SEARCH_TEXT_MAX_LEN = 150

#: name of the search bar's input field (also used by click-to-filter).
SEARCH_INPUT_NAME = "search_value"


class SearchKey(StrEnum):
    """Keys usable in a search query, e.g. `tag:python`."""

    FREE_TEXT = FREE_TEXT_KEY  # terms without a key
    TAG = "tag"
    USER = "user"
    EXERCISE = "exercise"
    TITLE = "title"
    DESCRIPTION = "description"


class FilterMixin(rx.State, mixin=True):
    """Mixin for filtering components."""

    # a list of search values, each a SearchTerm(key, value)
    search_values: list[SearchTerm] = []

    # valid search keys. Needs to be overridden by parent class
    search_keys: list[str] = []

    @abstractmethod
    @rx.event
    def load_filtered_data(self):
        """Implement in child state to load data after filter changes."""
        raise NotImplementedError

    @rx.event
    def add_search_value(self, form_data: dict[str, Any]):
        """Adds a search value to the list of search values."""
        raw_val = form_data[SEARCH_INPUT_NAME][:SEARCH_TEXT_MAX_LEN]
        for term in parse_query_keys(raw_val, self.search_keys):
            if term not in self.search_values:
                self.search_values.append(term)
        self.load_filtered_data()

    @rx.event
    def remove_search_value(self, key: str, value: str):
        """Removes the search term with the given key and value."""
        with contextlib.suppress(ValueError):
            self.search_values.remove(SearchTerm(key, value))
        self.load_filtered_data()
