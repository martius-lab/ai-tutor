"""Profile menu helpers for the main navbar."""

import reflex as rx

import aitutor.routes as routes
from aitutor.auth.state import SessionState
from aitutor.language_state import LanguageState
from aitutor.models import UserRole


def get_user_icon():
    """Return the profile icon that matches authentication and role state."""
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
    """Return the profile icon color for the current authentication state."""
    return rx.cond(
        SessionState.is_authenticated,
        "accent",
        "gray",
    )


def profile_menu_item(
    label: str | rx.vars.StringVar[str], icon: str, on_click
) -> rx.Component:
    """Create a shared account menu item."""
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


def profile_menu_actions() -> rx.Component:
    """Create account actions for an existing menu content area."""
    return rx.cond(
        SessionState.is_authenticated,
        rx.fragment(
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
            profile_menu_item(
                LanguageState.language_string,
                icon="languages",
                on_click=SessionState.toggle_language,
            ),
            profile_menu_item(
                LanguageState.user_settings,
                icon="cog",
                on_click=rx.redirect(routes.USER_SETTINGS),
            ),
            profile_menu_item(
                LanguageState.log_out,
                icon="log-out",
                on_click=SessionState.perform_logout,
            ),
        ),
        rx.fragment(
            profile_menu_item(
                LanguageState.language_string,
                icon="languages",
                on_click=SessionState.toggle_language,
            ),
            profile_menu_item(
                LanguageState.log_in,
                icon="log-in",
                on_click=lambda: rx.redirect(routes.LOGIN),
            ),
            profile_menu_item(
                LanguageState.register,
                icon="notepad-text",
                on_click=lambda: rx.redirect(routes.REGISTER),
            ),
        ),
    )


def profile_menu() -> rx.Component:
    """Create the profile menu component for the navigation bar."""

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
                profile_menu_actions(),
            ),
            rx.menu.content(
                profile_menu_actions(),
            ),
        ),
        justify="end",
    )
