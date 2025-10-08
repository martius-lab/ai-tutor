"""Page for the tutor/admin to see submissions."""

import reflex as rx

from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.submissions.components import (
    submissions_table,
    only_with_submissions,
)
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.utilities.filtering_components import search_bar, search_badges


@with_navbar(routes.SUBMISSIONS)
@page_require_role_at_least(UserRole.TUTOR)
def submissions_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            search_bar(SubmissionsState),
            only_with_submissions(),
            search_badges(SubmissionsState),
            submissions_table(),
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
