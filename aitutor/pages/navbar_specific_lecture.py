"""Specific lecture navbar."""

import reflex as rx

from aitutor.language_state import LanguageState

specific_lecture_links = [
    ("Lecture Overview", "lecture_overview", "layout-dashboard"),
    (LanguageState.exercises_link, "exercises", "book-open"),
    ("Members", "members", "users"),
    (LanguageState.settings, "settings", "settings"),
]


def tab_content(link):
    """
    The icon and text for a tab in the specific lecture navbar.

    This follows the same structure as the admin navbar to avoid layout shifts while
    icons are loading.
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


def specific_lecture_navbar(tab_to_highlight: str) -> rx.Component:
    """Create a navigation bar for pages inside one specific lecture."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.foreach(
                    specific_lecture_links,
                    lambda link: rx.tabs.trigger(
                        tab_content(link),
                        value=link[1],
                        disabled=link[1] != "lecture_overview",
                        _hover=rx.cond(
                            link[1] == "lecture_overview",
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
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


def with_specific_lecture_navbar(tab_to_highlight: str):
    """Decorator to add the specific lecture navigation bar to a page."""

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        return lambda: rx.vstack(
            specific_lecture_navbar(tab_to_highlight),
            component_factory(),
            spacing="0",
            padding="0",
            align="center",
            width="90%",
        )

    return decorator