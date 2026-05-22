"""Navigation link helpers for the main navbar."""

from dataclasses import dataclass
from typing import Optional

import reflex as rx

import aitutor.routes as routes
from aitutor.auth.protection import has_permission, lecture_has_role_at_least
from aitutor.language_state import LanguageState
from aitutor.models import GlobalPermission, UserRole


@dataclass
class NavbarLink:
    """Represents a navigation link in the navbar."""

    label: rx.vars.StringVar[str] | str
    route: str
    icon: str


def get_links():
    """Return the list of navigation links for the current user."""
    return [
        NavbarLink(LanguageState.home_link, routes.HOME, "house"),
        NavbarLink(LanguageState.exercises_link, routes.EXERCISES, "book"),
        NavbarLink(LanguageState.lectures_link, routes.MY_LECTURES, "graduation-cap"),
        rx.cond(
            lecture_has_role_at_least(UserRole.TUTOR),
            NavbarLink(
                LanguageState.submissions_link, routes.SUBMISSIONS, "search-check"
            ),
            None,
        ),
        rx.cond(
            lecture_has_role_at_least(UserRole.ADMIN)
            | has_permission(GlobalPermission.MAINTAINER),
            NavbarLink(
                LanguageState.admin_settings_link,
                routes.MANAGE_EXERCISES,
                "shield-check",
            ),
            None,
        ),
    ]


def is_highlighted(route_to_highlight: Optional[str], url: str) -> rx.Var[bool]:
    """Return whether a navigation link should be highlighted."""
    return rx.cond(
        route_to_highlight,
        rx.cond(
            route_to_highlight == routes.HOME,
            url == routes.HOME,
            url.startswith(route_to_highlight or ""),
        ),
        False,
    )


def navbar_link_desktop(
    link: NavbarLink, route_to_highlight: Optional[str]
) -> rx.Component:
    """Create a navigation link component for the desktop menu."""
    return rx.cond(
        is_highlighted(route_to_highlight, link.route),
        rx.link(
            rx.button(
                rx.text(link.label, size="4", weight="medium"),
                _hover={"cursor": "pointer"},
            ),
            href=link.route,
        ),
        rx.link(
            rx.text(link.label, size="4", weight="medium"),
            href=link.route,
        ),
    )


def navbar_link_mobile(link: NavbarLink, route_to_highlight: Optional[str]):
    """Create a navigation link component for the mobile menu."""
    return rx.menu.item(
        rx.cond(
            is_highlighted(route_to_highlight, link.route),
            rx.hstack(
                rx.icon(
                    link.icon,
                    size=15,
                    color=rx.color("accent", 9),
                ),
                rx.text(
                    link.label,
                    weight="bold",
                    color=rx.color("accent", 9),
                ),
                align="center",
            ),
            rx.hstack(
                rx.icon(link.icon, size=15),
                rx.text(link.label),
                align="center",
            ),
        ),
        on_click=rx.redirect(link.route),
        _hover={"cursor": "pointer"},
    )
