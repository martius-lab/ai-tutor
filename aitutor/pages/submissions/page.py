"""Page for the teacher to see submissions."""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.pages.submissions.components import submissions_table
from aitutor import routes


@with_navbar
@require_role_at_least(UserRole.TEACHER)
def submissions_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.button(
                    rx.icon("arrow-left", size=20),
                    color_scheme="iris",
                    on_click=rx.redirect(routes.EXERCISES),
                    _hover={"cursor": "pointer"},
                ),
                rx.heading(
                    f"Submissions for exercise: {SubmissionsState.exercise_title}",
                    size="8",
                ),
                padding_top="3em",
                padding_bottom="1em",
                align="center",
            ),
            submissions_table(),
            align="center",
            justify="center",
        ),
    )
