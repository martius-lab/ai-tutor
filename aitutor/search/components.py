"""UI components for searching tables: the search bar and the search badges."""

from types import MappingProxyType
from typing import NamedTuple

import reflex as rx
from reflex.vars import ArrayVar
from reflex_components_radix.themes.base import LiteralAccentColor

from aitutor.language_state import LanguageState
from aitutor.search.parser import SearchTerm
from aitutor.search.state import (
    SEARCH_INPUT_NAME,
    SEARCH_TEXT_MAX_LEN,
    FilterMixin,
    SearchKey,
)


class BadgeStyle(NamedTuple):
    """Icon and color of a search badge."""

    icon: str
    color: LiteralAccentColor


# Used for free text and for any key without its own style.
_FALLBACK_STYLE = BadgeStyle("search", "gray")

#: Badge style per search key (read-only).
BADGE_STYLES = MappingProxyType(
    {
        SearchKey.FREE_TEXT: _FALLBACK_STYLE,
        SearchKey.TAG: BadgeStyle("tag", "indigo"),
        SearchKey.USER: BadgeStyle("user-round", "cyan"),
        SearchKey.EXERCISE: BadgeStyle("book", "violet"),
        SearchKey.TITLE: BadgeStyle("book", "violet"),
        SearchKey.DESCRIPTION: BadgeStyle("book-open-text", "violet"),
    }
)


def search_bar(state: type[FilterMixin]) -> rx.Component:
    """Search bar for entering a search query."""
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
                name=SEARCH_INPUT_NAME,
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
    """Display the active search terms as badges, styled by their key."""

    def badge(term: ArrayVar[SearchTerm], style: BadgeStyle) -> rx.Component:
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

    def styled_badge(term: ArrayVar[SearchTerm]) -> rx.Component | rx.Var:
        cases = [(key, badge(term, style)) for key, style in BADGE_STYLES.items()]
        return rx.match(term[0], *cases, badge(term, _FALLBACK_STYLE))

    return rx.cond(
        state.search_values,
        rx.hstack(
            rx.foreach(state.search_values, styled_badge),
            spacing="2",
            wrap="wrap",
        ),
    )
