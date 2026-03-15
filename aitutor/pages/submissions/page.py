"""Page for the tutor/admin to see submissions."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import lecture_page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.submissions.components import submissions_table
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.utilities.filtering_components import search_badges, search_bar


@with_navbar(routes.SUBMISSIONS)
@lecture_page_require_role_at_least(UserRole.TUTOR)
def submissions_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            search_bar(SubmissionsState),
            search_badges(SubmissionsState),
            submissions_table(),
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
