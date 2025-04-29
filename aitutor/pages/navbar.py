"""
This module defines the navbar components for the Reflex application.
"""

import reflex as rx
import reflex_local_auth
from aitutor.auth.state import SessionState
from aitutor.auth.models import UserRole

links = [
    ("Home", "/"),
    ("Chat", "/chat"),
    ("Exercises", "/exercises"),
    ("Add Exercises", "/add-exercises"),
]


userrole = SessionState.authenticated_user_info.role


def navbar_link(text: str, url: str) -> rx.Component:
    """
    Creates a navigation link component.

    Args:
        text (str): The text to display for the link.
        url (str): The URL the link points to.

    Returns:
        rx.Component: A Reflex link component.
    """
    return rx.link(rx.text(text, size="4", weight="medium"), href=url)


def get_user_icon():
    """
    Determines the appropriate user icon based on the user's authentication and role.

    Returns:
        rx.Component: A Reflex conditional component representing the user icon.
    """
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
                    on_click=lambda: rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE),
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
                    on_click=lambda: rx.redirect(
                        reflex_local_auth.routes.REGISTER_ROUTE
                    ),
                    _hover={"cursor": "pointer"},
                ),
            ),
        ),
        justify="end",
    )


def navbar_default() -> rx.Component:
    """
    Creates the default navigation bar component for the application.

    Returns:
        rx.Component: A Reflex box component containing the navigation bar.
    """
    return rx.box(
        rx.desktop_only(
            rx.color_mode.button(position="bottom-left", type="button"),
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect("/"),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    *[navbar_link(text, url) for text, url in links],
                    spacing="5",
                ),
                profile_menu(),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.color_mode.button(position="bottom-left", type="button"),
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2em",
                        height="auto",
                        border_radius="25%",
                        on_click=rx.redirect("/"),
                        cursor="pointer",
                    ),
                    rx.heading("AI Tutor", size="6", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    rx.menu.root(
                        rx.menu.trigger(
                            rx.icon("menu", size=30),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.menu.content(
                            *[
                                rx.menu.item(
                                    text,
                                    on_click=lambda url=url: rx.redirect(url),
                                    _hover={"cursor": "pointer"},
                                )
                                for text, url in links
                            ]
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
        # position="fixed",
        # top="0px",
        # z_index="5",
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
        navbar_default(), component_factory(), spacing="0", padding="0", align="center"
    )
