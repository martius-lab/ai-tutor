"""Search state shared by all searchable pages."""

from abc import abstractmethod
from enum import StrEnum
from typing import Any

import reflex as rx
from sqlalchemy import ColumnElement

from aitutor.search.parser import (
    FREE_TEXT_KEY,
    SearchTerm,
    format_query,
    parse_query_keys,
)
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

    # the text in the search bar; kept in sync with `search_terms`
    search_text: str = ""

    @rx.var
    def search_keys(self) -> list[str]:
        """Keys the user can type, e.g. `tag:`; derived from `_search_fields`."""
        return [key for key in self._search_fields() if key != SearchKey.FREE_TEXT]

    @rx.var
    def has_multiple_search_terms(self) -> bool:
        """Whether more than one search term is active (shows "clear all")."""
        return len(self.search_terms) > 1

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
    def set_search_text(self, text: str):
        """Keeps the typed text in state (the input is controlled)."""
        self.search_text = text[:SEARCH_TEXT_MAX_LEN]

    @rx.event
    def submit_search(self, form_data: dict[str, Any]):
        """Replaces the filters with the ones in the search bar."""
        text = form_data[SEARCH_INPUT_NAME][:SEARCH_TEXT_MAX_LEN]
        self._set_search_terms(parse_query_keys(text, self.search_keys))

    @rx.event
    def add_search_term(self, form_data: dict[str, Any]):
        """Adds terms to the current filters (used by click-to-filter)."""
        raw_val = form_data[SEARCH_INPUT_NAME][:SEARCH_TEXT_MAX_LEN]
        new_terms = parse_query_keys(raw_val, self.search_keys)
        self._set_search_terms([*self.search_terms, *new_terms])

    @rx.event
    def remove_search_term(self, key: str, value: str):
        """Removes the search term with the given key and value."""
        removed = SearchTerm(key, value)
        self._set_search_terms([t for t in self.search_terms if t != removed])

    @rx.event
    def clear_search_terms(self):
        """Removes all search terms."""
        self._set_search_terms([])

    def _set_search_terms(self, terms: list[SearchTerm]):
        """Sets the filters, rewrites the search text to match, reloads."""
        self.search_terms = list(dict.fromkeys(terms))  # drop duplicates
        self.search_text = format_query(self.search_terms)
        self.load_filtered_data()

    def _search_condition(self) -> ColumnElement[bool]:
        """SQL condition for the current search terms, to use in `.where()`."""
        return build_search_condition(self.search_terms, self._search_fields())
