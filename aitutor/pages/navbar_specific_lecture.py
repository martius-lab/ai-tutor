"""Specific lecture navbar."""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState


def tab_content(label, icon):
    """
    The icon and text for a tab in the specific lecture navbar.

    This follows the same structure as the admin navbar to avoid layout shifts while
    icons are loading.
    """
    return rx.hstack(
        rx.box(
            rx.icon(icon, size=20),
            width="20px",
            height="20px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink=0,
        ),
        rx.text(label),
        spacing="2",
        align="center",
    )


def specific_lecture_navbar(tab_to_highlight: str) -> rx.Component:
    """Create a navigation bar for pages inside one specific lecture."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    tab_content("Lecture Overview", "layout-dashboard"),
                    value="lecture_overview",
                    on_click=rx.redirect(
                        routes.LECTURE_OVERVIEW
                        + "/"
                        + rx.State.router.page.params["lecture_id"].to(str)
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.tabs.trigger(
                    tab_content(LanguageState.exercises_link, "book-open"),
                    value="exercises",
                    disabled=True,
                    _hover={"cursor": "not-allowed"},
                ),
                rx.tabs.trigger(
                    tab_content("Members", "users"),
                    value="members",
                    on_click=rx.redirect(
                        routes.LECTURE_MEMBERS
                        + "/"
                        + rx.State.router.page.params["lecture_id"].to(str)
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.tabs.trigger(
                    tab_content(LanguageState.settings, "settings"),
                    value="settings",
                    disabled=True,
                    _hover={"cursor": "not-allowed"},
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
