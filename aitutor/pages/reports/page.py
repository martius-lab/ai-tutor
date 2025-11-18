"""reports page to report weird chats with Ai."""

import reflex as rx


from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least


@with_navbar(routes.REPORTS)
@page_require_role_at_least(UserRole.ADMIN)
def reports_page() -> rx.Component:
    """reports page."""
    return rx.center(
        rx.vstack(
            rx.text("Initialize reports page"),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
