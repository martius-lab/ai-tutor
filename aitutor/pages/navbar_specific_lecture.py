"""Specific lecture navbar."""

from typing import NamedTuple

import reflex as rx

import aitutor.routes as routes
from aitutor.auth.state import SessionState
from aitutor.language_state import LanguageState
from aitutor.utilities.lecture_permissions import (
    user_may_manage_lecture_exercises,
    user_may_view_lecture_submissions,
)


class SpecificLectureNavbarState(SessionState):
    """State for permissions needed by the specific lecture navbar."""

    @rx.var(initial_value=False)
    def can_view_submissions(self) -> bool:
        """Whether the current user may see the lecture submissions tab."""
        lecture_id = self._get_current_lecture_id()
        if lecture_id is None:
            return False

        with rx.session() as session:
            return user_may_view_lecture_submissions(
                session,
                user_id=self.authenticated_user.id,  # type: ignore[union-attr]
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )

    @rx.var(initial_value=False)
    def can_manage_exercises(self) -> bool:
        """Whether the current user may see the manage exercises tab."""
        lecture_id = self._get_current_lecture_id()
        if lecture_id is None:
            return False

        with rx.session() as session:
            return user_may_manage_lecture_exercises(
                session,
                user_id=self.authenticated_user.id,  # type: ignore[union-attr]
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )

    def _get_current_lecture_id(self) -> int | None:
        """Return the current lecture id from the route, if available and valid."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return None

        try:
            return int(self.lecture_id)
        except ValueError:
            return None


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
]

manage_exercises_link = SpecificLectureLink(
    label=LanguageState.manage_exercises_link,
    route=routes.LECTURE_MANAGE_EXERCISES,
    icon="book-copy",
    tab_value="manage_exercises",
    disabled=False,
)

submissions_link = SpecificLectureLink(
    label=LanguageState.submissions_link,
    route=routes.LECTURE_SUBMISSIONS,
    icon="search-check",
    tab_value="submissions",
    disabled=False,
)


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
                rx.cond(
                    SpecificLectureNavbarState.can_manage_exercises,
                    tab_trigger(manage_exercises_link, lecture_id),
                ),
                rx.cond(
                    SpecificLectureNavbarState.can_view_submissions,
                    tab_trigger(submissions_link, lecture_id),
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
