"""Search state shared by all searchable pages."""

import contextlib
from abc import abstractmethod

import reflex as rx

from aitutor.search.parser import SearchTerm, parse_query_keys

# maximum length of a search query typed by the user
SEARCH_TEXT_MAX_LEN = 150


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
    def add_search_value(self, form_data: dict):
        """Adds a search value to the list of search values."""
        raw_val = form_data["search_value"][:SEARCH_TEXT_MAX_LEN]
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
