"""Reports page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.reports.components import reports_table
from aitutor.pages.reports.state import ReportsState
from aitutor.utilities.filtering_components import search_badges, search_bar


@with_navbar(routes.REPORTS)
@page_require_role_at_least(UserRole.TUTOR)
def reports_page() -> rx.Component:
    """Page for tutors/admins to see all reports."""
    return rx.center(
        rx.vstack(
            search_bar(ReportsState),
            search_badges(ReportsState),
            reports_table(),
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
