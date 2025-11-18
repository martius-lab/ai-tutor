"""Reports page."""

import reflex as rx
from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from .components import reports_table
from .state import ReportsState

@with_navbar(routes.REPORTS)
@page_require_role_at_least(UserRole.TUTOR)
def reports_page() -> rx.Component:
    """Page for tutors/admins to see all reports."""
    return rx.center(
        rx.vstack(
            reports_table(),
            align="center",
            justify="center"
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
