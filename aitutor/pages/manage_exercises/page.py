"""Page add/edit exercises."""

import reflex as rx

from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.manage_exercises.components import (
    exercise_table,
    add_exercise_button,
    delete_selected_exercises_button,
)
from aitutor.utilities.filtering_components import search_bar, search_badges


@with_navbar(routes.MANAGE_EXERCISES)
@page_require_role_at_least(UserRole.ADMIN)
def manage_exercises_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            rx.desktop_only(
                rx.hstack(
                    search_bar(ManageExercisesState),
                    add_exercise_button(),
                    align="center",
                    justify="start",
                    width="100%",
                    name="top_bar_stack",
                ),
                width="100%",
            ),
            rx.mobile_and_tablet(
                rx.box(
                    add_exercise_button(),
                    margin_bottom="1em",
                )
            ),
            rx.mobile_and_tablet(
                search_bar(ManageExercisesState),
            ),
            search_badges(ManageExercisesState),
            rx.cond(
                ManageExercisesState.something_is_selected,
                rx.hstack(
                    delete_selected_exercises_button(),
                    align="start",
                    width="100%",
                    wrap="wrap",
                ),
            ),
            exercise_table(),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
