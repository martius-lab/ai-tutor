"""Page where the user can change their settings."""

import reflex as rx
import reflex_local_auth

from aitutor.language_state import LanguageState as LS
from aitutor.pages.navbar import with_navbar
from aitutor.pages.user_settings.components import change_password_card


@reflex_local_auth.require_login
@with_navbar()
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
