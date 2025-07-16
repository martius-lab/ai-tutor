"""
This module defines the navbar components for the Reflex application.
"""

import reflex as rx

from aitutor.auth.state import SessionState
from aitutor.models import UserRole
import aitutor.routes as routes
from aitutor.auth.protection import has_role_at_least


def navbar_link(text: str, url: str) -> rx.Component:
    """
    Creates a navigation link component.
    """
    return rx.link(rx.text(text, size="4", weight="medium"), href=url)


general_links = [
    ("Home", routes.HOME),
    ("Exercises", routes.EXERCISES),
]
teacher_links = [
    ("Submissions", routes.SUBMISSIONS),
]
admin_links = [
    ("Manage Exercises", routes.MANAGE_EXERCISES),
]


def get_links():
    """Returns the list of navigation links for the current user role."""
    return rx.cond(
        has_role_at_least(UserRole.ADMIN),
        general_links + teacher_links + admin_links,
        rx.cond(
            has_role_at_least(UserRole.TEACHER),
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
                    userrole == UserRole.TEACHER,
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
                            "log-out",
                            size=15,
                        ),
                        rx.text(
                            "Log out",
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
                            "log-in",
                            size=15,
                        ),
                        rx.text(
                            "Log in",
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
                            "Register",
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


def navbar() -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
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
                rx.hstack(
                    rx.foreach(
                        links,
                        lambda link: navbar_link(link[0], link[1]),
                    ),
                    spacing="5",
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
                            rx.foreach(
                                links,
                                lambda link: rx.menu.item(
                                    link[0],
                                    on_click=lambda url=link[1]: rx.redirect(url),
                                    _hover={"cursor": "pointer"},
                                ),
                            )
                        ),
                    ),
                    profile_menu(),
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        position="sticky",
        top="0px",
        z_index="1000",
        width="100%",
    )


def with_navbar(
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
        navbar(), component_factory(), spacing="0", padding="0", align="center"
    )
