"""Lecture section navbar."""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState

lecture_links = [
    (LanguageState.edit_lecture, routes.EDIT_LECTURE + "/new", "book-marked"),
]


def tab_content(link):
    """
    The icon and text for a tab in the lecture navbar.
    """
    return rx.hstack(
        rx.box(
            rx.icon(link[2], size=20),
            width="20px",
            height="20px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink=0,
        ),
        rx.text(link[0]),
        spacing="2",
        align="center",
    )


def lectures_navbar(tab_to_highlight: str) -> rx.Component:
    """Create a navigation bar for lecture-related pages."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.foreach(
                    lecture_links,
                    lambda link: rx.tabs.trigger(
                        tab_content(link),
                        value=link[1],
                        on_click=rx.redirect(link[1]),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                width="100%",
            ),
            default_value=tab_to_highlight,
            width="100%",
        ),
        margin_top="0.5em",
        width="100%",
    )


def with_lectures_navbar(tab_to_highlight: str):
    """Decorator to add the lecture navigation bar to a page."""

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        return lambda: rx.vstack(
            lectures_navbar(tab_to_highlight),
            component_factory(),
            spacing="0",
            padding="0",
            align="center",
            width="90%",
        )

    return decorator