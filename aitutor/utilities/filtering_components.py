"""Components that are used in the frontend for filtering tables"""

import contextlib
from abc import abstractmethod

import reflex as rx

from aitutor.global_vars import (
    SEARCH_EXERCISE_DESCRIPTION_KEY,
    SEARCH_EXERCISE_KEY,
    SEARCH_EXERCISE_TITLE_KEY,
    SEARCH_TAG_KEY,
    SEARCH_USER_KEY,
)
from aitutor.language_state import LanguageState
from aitutor.utilities.parser import parse_query_keys


class FilterMixin(rx.State, mixin=True):
    """Mixin for filtering components."""

    # a list of search values, each a tuple of (key, value)
    search_values: list[tuple[str, str]] = []

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
        parsed = parse_query_keys(form_data["search_value"], self.search_keys)
        if parsed not in self.search_values:
            self.search_values.append(parsed)
        self.load_filtered_data()

    @rx.event
    def remove_search_value(self, value: tuple[str, str]):
        """Removes a search value from the list."""
        with contextlib.suppress(ValueError):
            self.search_values.remove(tuple[str, str](value))
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
    """Display search badges for the current search values."""
    return rx.hstack(
        rx.foreach(
            state.search_values,
            lambda value: rx.badge(
                rx.hstack(
                    rx.cond(
                        value[0] == SEARCH_USER_KEY,
                        rx.icon("user-round", size=18),
                    ),
                    rx.cond(
                        value[0] == SEARCH_EXERCISE_KEY,
                        rx.icon("book", size=18),
                    ),
                    rx.cond(
                        value[0] == SEARCH_TAG_KEY,
                        rx.icon("tag", size=18),
                    ),
                    rx.cond(
                        value[0] == SEARCH_EXERCISE_TITLE_KEY,
                        rx.icon("book", size=18),
                    ),
                    rx.cond(
                        value[0] == SEARCH_EXERCISE_DESCRIPTION_KEY,
                        rx.icon("text", size=18),
                    ),
                    rx.text(value[1]),
                    rx.icon(
                        "x",
                        on_click=state.remove_search_value(value),
                        _hover={"cursor": "pointer"},
                    ),
                    spacing="1",
                    align="center",
                ),
                variant="solid",
            ),
        ),
        spacing="2",
        wrap="wrap",
    )
