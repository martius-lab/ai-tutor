"""Specific lecture navbar."""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState

specific_lecture_links = [
    (
        "Lecture Overview",
        routes.LECTURE_OVERVIEW,
        "layout-dashboard",
        "lecture_overview",
        False,
    ),
    (
        LanguageState.exercises_link,
        routes.LECTURE_OVERVIEW,
        "book-open",
        "exercises",
        True,
    ),
    ("Members", routes.LECTURE_MEMBERS, "users", "members", False),
    (LanguageState.settings, routes.LECTURE_OVERVIEW, "settings", "settings", True),
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


def lecture_route(route: str, lecture_id) -> rx.Var[str]:
    """Return a lecture-specific route for the loaded lecture id."""
    return rx.cond(
        lecture_id,
        route + "/" + lecture_id.to(str),
        routes.MY_LECTURES,
    )


def tab_trigger(link, lecture_id) -> rx.Component:
    """Create one tab trigger for the specific lecture navbar."""
    return rx.tabs.trigger(
        tab_content(link),
        value=link[3],
        disabled=link[4],
        on_click=rx.redirect(lecture_route(link[1], lecture_id)),
        _hover={"cursor": rx.cond(link[4], "not-allowed", "pointer")},
    )


def specific_lecture_navbar(tab_to_highlight: str, lecture_id) -> rx.Component:
    """Create a navigation bar for pages inside one specific lecture."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.foreach(
                    specific_lecture_links,
                    lambda link: tab_trigger(link, lecture_id),
                ),
                width="100%",
            ),
            default_value=tab_to_highlight,
            width="100%",
        ),
        margin_top="0.5em",
        width="100%",
    )


def with_specific_lecture_navbar(tab_to_highlight: str, lecture_id):
    """Decorator to add the specific lecture navigation bar to a page."""

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        return lambda: rx.vstack(
            specific_lecture_navbar(tab_to_highlight, lecture_id),
            component_factory(),
            spacing="0",
            padding="0",
            align="center",
            width="90%",
        )

    return decorator
