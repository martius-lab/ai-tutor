"""Page for the teacher to see submissions."""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.submissions.components import (
    submissions_table,
    search_badges,
    search_bar,
    only_with_submissions,
)


@with_navbar
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
            search_bar(),
            only_with_submissions(),
            search_badges(),
            submissions_table(),
            align="center",
            justify="center",
        ),
    )
