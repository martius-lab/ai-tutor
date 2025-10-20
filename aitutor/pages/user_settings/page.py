"""Page where the user can change their settings."""

import reflex as rx

from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor import routes


@with_navbar(routes.EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def user_settings_page() -> rx.Component:
    """Page where the user can change their settings."""
    return rx.center(
        rx.card(rx.text("User Settings Page")),
        width="100%",
        padding="4",
    )
