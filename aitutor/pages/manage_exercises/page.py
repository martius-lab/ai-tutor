"""Page add/edit exercises."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.manage_exercises.components import (
    add_exercise_button,
    delete_selected_exercises_button,
    edit_tags_button,
    exercise_table,
    export_selected_exercises_button,
    import_exercises_button,
)
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


def exercise_toolbar() -> rx.Component:
    """Render grouped actions for managing exercises."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    import_exercises_button(),
                    add_exercise_button(),
                    edit_tags_button(),
                    class_name="exercise-toolbar-group",
                ),
                rx.hstack(
                    delete_selected_exercises_button(),
                    export_selected_exercises_button(),
                    class_name="exercise-toolbar-group",
                ),
                class_name="exercise-toolbar-row",
                width="100%",
            ),
            rx.hstack(
                search_bar(ManageExercisesState),
                class_name="exercise-search-row",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        class_name="exercise-toolbar",
    )


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.MANAGE_EXERCISES)
@page_require_role_or_permission(required_role=UserRole.ADMIN)
def manage_exercises_page() -> rx.Component:
    """Manage exercises page."""
    return rx.center(
        rx.vstack(
            exercise_toolbar(),
            search_badges(ManageExercisesState),
            exercise_table(),
            spacing="3",
            align="center",
            justify="start",
            width="100%",
        ),
        class_name="page-frame",
    )
