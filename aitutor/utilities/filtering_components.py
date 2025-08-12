"""Components that are used in the frontend for filtering tables"""

import reflex as rx
from aitutor.global_vars import SEARCH_USER_KEY, SEARCH_EXERCISE_KEY, SEARCH_TAG_KEY


def search_bar(state, keys_info: str) -> rx.Component:
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
                        rx.text(
                            "Search with 'key:searchValue' or "
                            "'key:\"search value\"' "
                            "to search a specific column."
                        ),
                        rx.text(f"keys: {keys_info}"),
                        rx.text("Without using 'key:' it searches in all columns."),
                    ),
                ),
            ),
            rx.input(
                rx.input.slot(rx.icon("search")),
                name="search_value",
                placeholder="tag:tagname",
                required=True,
            ),
            rx.button(
                rx.icon("plus"),
                _hover={"cursor": "pointer"},
            ),
            justify="center",
            align="center",
        ),
        on_submit=state.add_search_value,  # needs to be called the same in all states
        reset_on_submit=True,
    )


def search_badges(state) -> rx.Component:
    """Display search badges for the current search values."""
    return rx.hstack(
        rx.foreach(
            state.search_values,  # needs to be called the same in all states
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
                    rx.text(value[1]),
                    rx.icon(
                        "x",
                        on_click=state.remove_search_value(
                            value
                        ),  # needs to be called the same in all states
                        _hover={"cursor": "pointer"},
                    ),
                    spacing="1",
                    align="center",
                ),
                variant="solid",
                color_scheme="blue",
            ),
        ),
        spacing="2",
        wrap="wrap",
    )
