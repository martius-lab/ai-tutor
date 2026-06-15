"""Specific lecture navbar."""

from typing import NamedTuple

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState


class SpecificLectureLink(NamedTuple):
    """Configuration for one tab in the specific lecture navbar."""

    label: rx.Var[str]
    route: str
    icon: str
    tab_value: str
    disabled: bool


specific_lecture_links = [
    SpecificLectureLink(
        label=LanguageState.overview,
        route=routes.LECTURE_OVERVIEW,
        icon="layout-dashboard",
        tab_value="lecture_overview",
        disabled=False,
    ),
    SpecificLectureLink(
        label=LanguageState.exercises_link,
        route=routes.LECTURE_EXERCISES,
        icon="book-open",
        tab_value="exercises",
        disabled=False,
    ),
    SpecificLectureLink(
        label=LanguageState.members,
        route=routes.LECTURE_MEMBERS,
        icon="users",
        tab_value="members",
        disabled=False,
    ),
    SpecificLectureLink(
        label=LanguageState.manage_exercises_link,
        route=routes.LECTURE_MANAGE_EXERCISES,
        icon="book-copy",
        tab_value="manage_exercises",
        disabled=False,
    ),
]


def tab_content(link: SpecificLectureLink):
    """
    The icon and text for a tab in the specific lecture navbar.

    This follows the same structure as the admin navbar to avoid layout shifts while
    icons are loading.
    """
    return rx.hstack(
        rx.box(
            rx.icon(link.icon, size=20),
            width="20px",
            height="20px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink=0,
        ),
        rx.text(link.label),
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


def tab_trigger(link: SpecificLectureLink, lecture_id) -> rx.Component:
    """Create one tab trigger for the specific lecture navbar."""
    return rx.tabs.trigger(
        tab_content(link),
        value=link.tab_value,
        disabled=link.disabled,
        on_click=rx.redirect(lecture_route(link.route, lecture_id)),
        _hover={"cursor": rx.cond(link.disabled, "not-allowed", "pointer")},
    )


def specific_lecture_navbar(tab_to_highlight: str, lecture_id) -> rx.Component:
    """Create a navigation bar for pages inside one specific lecture."""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                *[tab_trigger(link, lecture_id) for link in specific_lecture_links],
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
