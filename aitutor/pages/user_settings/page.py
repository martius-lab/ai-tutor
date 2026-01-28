"""Page where the user can change their settings."""

import reflex as rx

from aitutor.auth.protection import page_require_role_at_least
from aitutor.language_state import LanguageState as LS
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.user_settings.components import change_password_card


@with_navbar()
@page_require_role_at_least(UserRole.STUDENT)
def user_settings_page() -> rx.Component:
    """Page where the user can change their settings."""
    return rx.center(
        rx.vstack(
            rx.heading(LS.user_settings),
            change_password_card(),
            width="100%",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
