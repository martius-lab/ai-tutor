"""Page for the teacher to add new exercises."""

import reflex as rx

from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.manage_exercises.components import (
    exercise_table,
    add_exercise_button,
)
from aitutor.utilities.filtering_components import search_bar, search_badges


@with_navbar(routes.MANAGE_EXERCISES)
@page_require_role_at_least(UserRole.ADMIN)
def manage_exercises_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            search_bar(ManageExercisesState),
            search_badges(ManageExercisesState),
            exercise_table(),
            rx.box(
                add_exercise_button(),
                margin_top="1em",
            ),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
