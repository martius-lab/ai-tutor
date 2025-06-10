"""Page for the teacher to add new exercises."""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.pages.manage_exercises.components import exercise_table


@with_navbar
@require_role_at_least(UserRole.ADMIN)
def manage_exercises_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            rx.center(
                rx.heading("Exercises", size="8", padding_top="2em"),
                padding_bottom="2em",
                width="100%",
            ),
            exercise_table(),
        ),
    )
