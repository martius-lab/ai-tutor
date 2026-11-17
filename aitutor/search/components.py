"""UI components for searching tables: the search bar and the search badges."""

import reflex as rx
from reflex.vars import ArrayVar

from aitutor.language_state import LanguageState
from aitutor.search.keys import FREE_TEXT, SEARCH_KEYS, SearchKey
from aitutor.search.parser import SearchTerm
from aitutor.search.state import SEARCH_TEXT_MAX_LEN, FilterMixin


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
                    on_click=state.remove_search_value(term[0], term[1]),
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
