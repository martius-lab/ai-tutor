"""Components that are used in the frontend for filtering tables"""

import contextlib
from abc import abstractmethod
from typing import NamedTuple

import reflex as rx
from reflex.vars import ArrayVar
from reflex_components_radix.themes.base import LiteralAccentColor

from aitutor.language_state import LanguageState
from aitutor.utilities.parser import FREE_TEXT_KEY, SearchTerm, parse_query_keys

# maximum length of a search query typed by the user
SEARCH_TEXT_MAX_LEN = 150


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
    def remove_search_value(self, value: SearchTerm):
        """Removes a search value from the list."""
        with contextlib.suppress(ValueError):
            self.search_values.remove(SearchTerm(*value))
        self.load_filtered_data()


def search_bar(state: type[FilterMixin]) -> rx.Component:
    """Search bar for the input of search values."""
    return rx.form.root(
        rx.hstack(
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.icon("info"),
                    _hover={"cursor": "pointer"},
                ),
                rx.dialog.content(
                    rx.vstack(
                        rx.markdown(
                            LanguageState.search_info,
                            style={
                                "& p": {"margin": "0"},
                            },
                        ),
                        rx.markdown(
                            f"**Keys:** {state.search_keys}",
                            style={"& p": {"margin": "1"}},
                        ),
                    ),
                ),
            ),
            rx.input(
                rx.input.slot(rx.icon("search")),
                name="search_value",
                placeholder=LanguageState.search_placeholder,
                required=True,
                max_width="60vw",
                max_length=SEARCH_TEXT_MAX_LEN,
            ),
            rx.button(
                rx.icon("plus"),
                _hover={"cursor": "pointer"},
            ),
            justify="center",
            align="center",
        ),
        on_submit=state.add_search_value,
        reset_on_submit=True,
    )


def search_badges(state: type[FilterMixin]) -> rx.Component:
    """Display search badges, styled by their key."""

    def badge(term: ArrayVar[SearchTerm], style: SearchKey) -> rx.Component:
        return rx.badge(
            rx.hstack(
                rx.icon(style.icon, size=16),
                rx.text(term[1]),
                rx.icon(
                    "x",
                    on_click=state.remove_search_value(term),
                    _hover={"cursor": "pointer"},
                ),
                spacing="1",
                align="center",
            ),
            color_scheme=style.color,
            variant="soft",
        )

    def styled_badge(term: ArrayVar[SearchTerm]):
        cases = [(k.key, badge(term, k)) for k in SEARCH_KEYS]
        return rx.match(term[0], *cases, badge(term, FREE_TEXT))

    return rx.hstack(
        rx.foreach(state.search_values, styled_badge), spacing="2", wrap="wrap"
    )
