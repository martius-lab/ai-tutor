"""Search state shared by all searchable pages."""

import contextlib
from abc import abstractmethod
from enum import StrEnum
from typing import Any

import reflex as rx
from sqlalchemy import ColumnElement

from aitutor.search.parser import FREE_TEXT_KEY, SearchTerm, parse_query_keys
from aitutor.search.query import SearchFields, build_search_condition

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


class SearchMixin(rx.State, mixin=True):
    """Mixin for search components to filter records."""

    # a list of search terms, each a SearchTerm(key, value)
    search_terms: list[SearchTerm] = []

    @rx.var
    def search_keys(self) -> list[str]:
        """Keys the user can type, e.g. `tag:`; derived from `_search_fields`."""
        return [key for key in self._search_fields() if key != SearchKey.FREE_TEXT]

    @classmethod
    @abstractmethod
    def _search_fields(cls) -> SearchFields:
        """The page's searchable fields, e.g. title, description."""
        raise NotImplementedError

    @abstractmethod
    @rx.event
    def load_filtered_data(self):
        """Implement in child state to load data after filter changes."""
        raise NotImplementedError

    @rx.event
    def add_search_term(self, form_data: dict[str, Any]):
        """Adds a search term to the list of search terms."""
        raw_val = form_data[SEARCH_INPUT_NAME][:SEARCH_TEXT_MAX_LEN]
        for term in parse_query_keys(raw_val, self.search_keys):
            if term not in self.search_terms:
                self.search_terms.append(term)
        self.load_filtered_data()

    @rx.event
    def remove_search_term(self, key: str, value: str):
        """Removes the search term with the given key and value."""
        with contextlib.suppress(ValueError):
            self.search_terms.remove(SearchTerm(key, value))
        self.load_filtered_data()

    def _search_condition(self) -> ColumnElement[bool]:
        """SQL condition for the current search terms, to use in `.where()`."""
        return build_search_condition(self.search_terms, self._search_fields())
