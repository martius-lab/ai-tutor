"""
This module defines the navbar components for the Reflex application.
"""

import reflex as rx

from aitutor.auth.state import SessionState
from aitutor.models import UserRole
import aitutor.routes as routes
from aitutor.auth.protection import has_role_at_least
from aitutor.config import get_config
from aitutor.language_state import LanguageState


def navbar_link(text: str, url: str, route_to_highlight) -> rx.Component:
    """
    Creates a navigation link component.
    """
    return rx.cond(
        url == route_to_highlight,
        rx.link(
            rx.button(
                rx.text(text, size="4", weight="medium"), _hover={"cursor": "pointer"}
            ),
            href=url,
        ),
        rx.link(
            rx.text(text, size="4", weight="medium"),
            href=url,
        ),
    )


general_links = [
    (LanguageState.home_link, routes.HOME, "house"),
    (LanguageState.exercises_link, routes.EXERCISES, "book"),
]
teacher_links = [
    (LanguageState.submissions_link, routes.SUBMISSIONS, "search-check"),
]
admin_links = [
    (LanguageState.manage_exercises_link, routes.MANAGE_EXERCISES, "pencil-line"),
    (LanguageState.manage_users, routes.MANAGE_USERS, "users"),
]


def get_links():
    """Returns the list of navigation links for the current user role."""
    return rx.cond(
        has_role_at_least(UserRole.ADMIN),
        general_links + teacher_links + admin_links,
        rx.cond(
            has_role_at_least(UserRole.TUTOR),
            general_links + teacher_links,
            general_links,
        ),
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
                    rx.icon(
                        "circle-user-round",
                        size=15,
                    ),
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
                rx.menu.item(
                    rx.hstack(
                        rx.icon(
                            "languages",
                            size=15,
                        ),
                        rx.text(
                            LanguageState.language_string,
                            size="2",
                            margin_bottom="6px",
                            margin_top="6px",
                        ),
                        align="center",
                        justify="center",
                        spacing="1",
                    ),
                    on_click=SessionState.toggle_language,
                    _hover={"cursor": "pointer"},
                ),
                rx.menu.item(
                    rx.hstack(
                        rx.icon(
                            "log-out",
                            size=15,
                        ),
                        rx.text(
                            LanguageState.log_out,
                            size="2",
                            margin_bottom="6px",
                            margin_top="6px",
                        ),
                        align="center",
                        justify="center",
                        spacing="1",
                    ),
                    on_click=SessionState.perform_logout(),  # type: ignore
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.hstack(
                        rx.icon(
                            "languages",
                            size=15,
                        ),
                        rx.text(
                            LanguageState.language_string,
                            size="2",
                            margin_bottom="6px",
                            margin_top="6px",
                        ),
                        align="center",
                        justify="center",
                        spacing="1",
                    ),
                    on_click=SessionState.toggle_language,
                    _hover={"cursor": "pointer"},
                ),
                rx.menu.item(
                    rx.hstack(
                        rx.icon(
                            "log-in",
                            size=15,
                        ),
                        rx.text(
                            LanguageState.log_in,
                            size="2",
                            margin_bottom="6px",
                            margin_top="6px",
                        ),
                        align="center",
                        justify="center",
                        spacing="1",
                    ),
                    on_click=lambda: rx.redirect(routes.LOGIN),
                    _hover={"cursor": "pointer"},
                ),
                rx.menu.item(
                    rx.hstack(
                        rx.icon(
                            "notepad-text",
                            size=15,
                        ),
                        rx.text(
                            LanguageState.register,
                            size="2",
                            margin_bottom="6px",
                            margin_top="6px",
                        ),
                        align="center",
                        justify="center",
                        spacing="1",
                    ),
                    on_click=lambda: rx.redirect(routes.REGISTER),
                    _hover={"cursor": "pointer"},
                ),
            ),
        ),
        justify="end",
    )


def navbar(route_to_highlight: str) -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Args:
        route_to_highlight (str): The route that identifies which link to highlight
        in the navbar.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
    config = get_config()
    links = get_links()
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
                    rx.text(config.course_name, weight="bold"),
                    rx.hstack(
                        rx.foreach(
                            links,
                            lambda link: navbar_link(
                                link[0], link[1], route_to_highlight
                            ),
                        ),
                        spacing="5",
                        align="center",
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
                                    config.course_name,
                                    color_scheme="gray",
                                    weight="bold",
                                ),
                                padding="0.5em",
                            ),
                            rx.separator(),
                            rx.foreach(
                                links,
                                lambda link: rx.menu.item(
                                    rx.cond(
                                        link[1] == route_to_highlight,
                                        rx.hstack(
                                            rx.icon(link[2], size=15, color="#0d74ce"),
                                            rx.text(
                                                link[0],
                                                weight="bold",
                                                color="#0d74ce",
                                            ),
                                            align="center",
                                        ),
                                        rx.hstack(
                                            rx.icon(link[2], size=15),
                                            rx.text(link[0]),
                                            align="center",
                                        ),
                                    ),
                                    on_click=rx.redirect(link[1]),
                                    _hover={"cursor": "pointer"},
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


def with_navbar(route_to_highlight: str):
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
