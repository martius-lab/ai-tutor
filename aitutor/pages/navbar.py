"""
This module defines the navbar components for the Reflex application.
"""

from dataclasses import dataclass
from typing import Optional

import reflex as rx

import aitutor.routes as routes
from aitutor import DisplayConfigState
from aitutor.auth.protection import has_permission, lecture_has_role_at_least
from aitutor.auth.state import SessionState
from aitutor.language_state import LanguageState
from aitutor.models import GlobalPermission, UserRole


@dataclass
class NavbarLink:
    """Represents a navigation link in the navbar.

    Attributes:
        label: The display text for the link.
        route: The URL route the link points to.
        icon: The name of the icon to display alongside the link.
    """

    label: rx.vars.StringVar[str] | str
    route: str
    icon: str


def get_links():
    """Returns the list of navigation links for the current user.

    Which links are included depends on the user's permissions.

    Returns:
        list[tuple[str, str, str]]: A list of tuples each representing one link.  Tuple
            items are (label, route, icon).
    """
    return [
        NavbarLink(LanguageState.home_link, routes.HOME, "house"),
        NavbarLink(LanguageState.exercises_link, routes.EXERCISES, "book"),
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
    """
    Determines if a navigation link should be highlighted based on the current route.
    """
    return rx.cond(
        route_to_highlight,  # None check
        rx.cond(
            route_to_highlight == routes.HOME,
            url == routes.HOME,
            url.startswith(route_to_highlight or ""),  # None handled by outer cond
        ),
        False,
    )


def navbar_link_desktop(
    link: NavbarLink, route_to_highlight: Optional[str]
) -> rx.Component:
    """Creates a navigation link component for the desktop menu.

    Args:
        link: Information about the link to create.
        route_to_highlight:  The route that should be highlighted as selected.
    """
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
    """Creates a navigation link component for the mobile menu.

    Args:
        link: Information about the link to create.
        route_to_highlight:  The route that should be highlighted as selected.
    """
    return rx.menu.item(
        rx.cond(
            # check if the link should be highlighted
            is_highlighted(route_to_highlight, link.route),
            rx.hstack(
                # highlighted link
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
                # non-highlighted link
                rx.icon(link.icon, size=15),
                rx.text(link.label),
                align="center",
            ),
        ),
        on_click=rx.redirect(link.route),
        _hover={"cursor": "pointer"},
    )


def get_user_icon():
    """
    Determines the appropriate user icon based on the user's authentication and role.

    Returns:
        rx.Component: A Reflex conditional component representing the user icon.
    """
    userrole = SessionState.user_role
    return rx.cond(
        ~SessionState.is_authenticated,
        "user-round",
        rx.cond(
            userrole == UserRole.STUDENT,
            "user-round-check",
            rx.cond(
                userrole == UserRole.ADMIN,
                "user-round-cog",
                rx.cond(
                    userrole == UserRole.TUTOR,
                    "user-round-search",
                    "user-round",
                ),
            ),
        ),
    )


def get_user_icon_color():
    """
    Determines the appropriate color for the user icon based on
    the user's authentication and role.

    Returns:
        str: The color for the user icon.
    """
    return rx.cond(
        SessionState.is_authenticated,
        "accent",
        "gray",
    )


def profile_menu() -> rx.Component:
    """
    Creates a profile menu component for the navigation bar.

    Returns:
        rx.Component: A Reflex menu component with login/registration/logout options.
    """

    def menu_item(
        label: str | rx.vars.StringVar[str], icon: str, on_click
    ) -> rx.Component:
        return rx.menu.item(
            rx.hstack(
                rx.icon(icon, size=15),
                rx.text(
                    label,
                    size="2",
                    margin_bottom="6px",
                    margin_top="6px",
                ),
                align="center",
                justify="center",
                spacing="1",
            ),
            on_click=on_click,
            _hover={"cursor": "pointer"},
        )

    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(
                rx.icon(get_user_icon()),
                size="2",
                radius="full",
                _hover={"cursor": "pointer"},
                background_color=get_user_icon_color(),
            ),
        ),
        rx.cond(
            SessionState.is_authenticated,
            rx.menu.content(
                rx.hstack(
                    rx.icon("circle-user-round", size=15),
                    rx.text(
                        {SessionState.authenticated_user.username},
                        size="2",
                        margin_bottom="6px",
                        margin_top="6px",
                    ),
                    align="center",
                    justify="center",
                    spacing="1",
                ),
                rx.separator(),
                menu_item(
                    LanguageState.language_string,
                    icon="languages",
                    on_click=SessionState.toggle_language,
                ),
                menu_item(
                    LanguageState.user_settings,
                    icon="cog",
                    on_click=rx.redirect(routes.USER_SETTINGS),
                ),
                menu_item(
                    LanguageState.log_out,
                    icon="log-out",
                    on_click=SessionState.perform_logout,
                ),
            ),
            rx.menu.content(
                menu_item(
                    LanguageState.language_string,
                    icon="languages",
                    on_click=SessionState.toggle_language,
                ),
                menu_item(
                    LanguageState.log_in,
                    icon="log-in",
                    on_click=lambda: rx.redirect(routes.LOGIN),
                ),
                menu_item(
                    LanguageState.register,
                    icon="notepad-text",
                    on_click=lambda: rx.redirect(routes.REGISTER),
                ),
            ),
        ),
        justify="end",
    )


def navbar(route_to_highlight: Optional[str]) -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Args:
        route_to_highlight (str): The route that identifies which link to highlight
        in the navbar.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect(routes.HOME),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.vstack(
                    rx.text(DisplayConfigState.course_name, weight="bold"),
                    rx.hstack(
                        rx.foreach(
                            get_links(),
                            lambda link: rx.cond(
                                link != None,
                                navbar_link_desktop(link, route_to_highlight),
                            ),
                        ),
                        spacing="5",
                        align="center",
                        wrap="wrap",
                    ),
                    align="center",
                ),
                rx.hstack(
                    rx.color_mode.button(),
                    profile_menu(),
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect(routes.HOME),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="6", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    rx.color_mode.button(),
                    rx.menu.root(
                        rx.menu.trigger(
                            rx.icon("menu", size=30),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.menu.content(
                            rx.box(
                                rx.text(
                                    DisplayConfigState.course_name,
                                    color_scheme="gray",
                                    weight="bold",
                                ),
                                padding="0.5em",
                            ),
                            rx.separator(),
                            rx.foreach(
                                get_links(),
                                lambda link: rx.cond(
                                    link != None,
                                    navbar_link_mobile(link, route_to_highlight),
                                ),
                            ),
                            max_width="90vw",
                        ),
                    ),
                    profile_menu(),
                ),
                justify="between",
                align_items="center",
                width="100%",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        width="100%",
    )


def with_navbar(route_to_highlight: Optional[str] = None):
    """
    Decorator to add a navigation bar to a component.

    Args:
        route_to_highlight (str): The route that identifies which link to highlight
        in the navbar.
    """

    def decorator(
        component_factory: rx.app.ComponentCallable,
    ) -> rx.app.ComponentCallable:
        """
        Decorator to add a navigation bar to a component.

        Args:
            component_factory (rx.app.ComponentCallable):
            A callable that returns a Reflex component.

        Returns:
            rx.app.ComponentCallable:
            A callable that returns a Reflex component with the navigation bar.
        """
        return lambda: rx.vstack(
            navbar(route_to_highlight),
            component_factory(),
            spacing="0",
            padding="0",
            align="center",
        )

    return decorator
