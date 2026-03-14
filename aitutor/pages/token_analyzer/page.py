"""Token Analyzer page (placeholder)."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.TOKEN_ANALYZER)
@page_require_role_at_least(UserRole.ADMIN)
def token_analyzer_page() -> rx.Component:
    """Placeholder page for the token analyzer feature."""
    return rx.center(
        rx.vstack(
            rx.heading("Token Analyzer", size="6"),
            rx.text("empty"),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
