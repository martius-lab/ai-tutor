"""Page for the teacher to see submissions."""

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
@page_require_role_at_least(UserRole.TEACHER)
def submissions_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            rx.heading(
                "Submissions",
                size="8",
                padding_top="1em",
                padding_bottom="0.5em",
                align="center",
            ),
            search_bar(SubmissionsState),
            only_with_submissions(),
            search_badges(SubmissionsState),
            submissions_table(),
            align="center",
            justify="center",
            padding_bottom="2em",
        ),
    )
