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
    SearchKey,
    SearchMixin,
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


def key_chip(key: rx.Var[str]) -> rx.Component | rx.Var:
    """A search key shown with its badge icon and color, e.g. in the help."""

    def chip(style: BadgeStyle) -> rx.Component:
        return rx.badge(
            rx.icon(style.icon, size=14),
            rx.code(key, variant="ghost"),
            color_scheme=style.color,
            variant="soft",
            radius="full",
        )

    cases = [(k, chip(style)) for k, style in BADGE_STYLES.items()]
    return rx.match(key, *cases, chip(_FALLBACK_STYLE))


def search_help(state: type[SearchMixin]) -> rx.Component:
    """Help dialog: the search syntax and the keys of this page."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.icon_button(
                rx.icon("info", size=18),
                variant="ghost",
                color_scheme="gray",
                radius="full",
                type="button",
                _hover={"cursor": "pointer"},
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                rx.markdown(
                    LanguageState.search_info,
                    style={"& p": {"margin": "0"}},
                ),
                rx.text(LanguageState.search_filters_label, weight="bold"),
                rx.hstack(
                    rx.foreach(state.search_keys, key_chip),
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="3",
            ),
        ),
    )


def _search_input(state: type[SearchMixin], **props) -> rx.Component:
    """Search bar for entering a search query.

    Fills the width of its parent; wrap it in a container to control its size.
    """
    return rx.form.root(
        rx.input(
            rx.input.slot(rx.icon("search", size=18)),
            rx.input.slot(
                search_help(state),
                rx.button(
                    LanguageState.search_submit,
                    type="submit",
                    radius="full",
                    size="2",
                    _hover={"cursor": "pointer"},
                ),
                gap="2",
                padding_right="4px",
            ),
            name=SEARCH_INPUT_NAME,
            placeholder=LanguageState.search_placeholder,
            value=state.search_text,
            on_change=state.set_search_text,
            max_length=SEARCH_TEXT_MAX_LEN,
            enter_key_hint="search",
            size="3",
            radius="full",
            variant="surface",
            width="100%",
        ),
        on_submit=state.submit_search,
        width="100%",
        **props,
    )


def search_bar(state: type[SearchMixin]) -> rx.Component:
    """Search input with the active search terms shown as badges below it."""
    return rx.vstack(
        _search_input(state),
        search_badges(state),
        spacing="4",
        width="100%",
    )


def search_badges(state: type[SearchMixin]) -> rx.Component:
    """Display the active search terms as badges, styled by their key."""

    def badge(
        term: ArrayVar[SearchTerm],
        style: BadgeStyle,
        label: str | rx.Var[str] | None,
    ) -> rx.Component:
        children: list[rx.Component] = [rx.icon(style.icon, size=16)]
        if label is not None:  # not `if label:`, which fails for Vars
            children.append(rx.text(f"{label}:", opacity="0.7"))
        children += [
            rx.text(term[1]),
            rx.icon(
                "x",
                on_click=state.remove_search_term(term[0], term[1]),
                _hover={"cursor": "pointer"},
            ),
        ]
        return rx.badge(
            rx.hstack(*children, spacing="1", align="center"),
            color_scheme=style.color,
            variant="soft",
            radius="full",
            size="2",
        )

    def styled_badge(term: ArrayVar[SearchTerm]) -> rx.Component | rx.Var:
        cases = [
            (key, badge(term, style, None if key == SearchKey.FREE_TEXT else key))
            for key, style in BADGE_STYLES.items()
        ]
        return rx.match(term[0], *cases, badge(term, _FALLBACK_STYLE, term[0]))

    return rx.cond(
        state.search_terms,
        rx.hstack(
            rx.foreach(state.search_terms, styled_badge),
            rx.cond(
                state.has_multiple_search_terms,
                rx.button(
                    LanguageState.clear_search,
                    on_click=state.clear_search_terms,
                    variant="surface",
                    color_scheme="gray",
                    size="1",
                    radius="full",
                ),
            ),
            spacing="2",
            wrap="wrap",
            align="center",
            justify="center",
            width="100%",
        ),
    )
