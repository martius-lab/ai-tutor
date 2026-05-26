"""Page add/edit exercises."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.lecture_manage_exercises.components import (
    add_exercise_button,
    delete_selected_exercises_button,
    edit_tags_button,
    exercise_table,
    export_selected_exercises_button,
    import_exercises_button,
)
from aitutor.pages.lecture_manage_exercises.state import LectureManageExercisesState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar
from aitutor.utilities.filtering_components import search_badges, search_bar


@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "manage_exercises",
    LectureManageExercisesState.current_lecture_id,
)
@page_require_role_or_permission(required_role=UserRole.STUDENT)
def lecture_manage_exercises_page() -> rx.Component:
    """Manage lecture-specific exercises page."""
    return rx.center(
        rx.vstack(
            rx.desktop_only(
                rx.hstack(
                    rx.hstack(
                        delete_selected_exercises_button(),
                        export_selected_exercises_button(),
                    ),
                    rx.hstack(
                        import_exercises_button(),
                        add_exercise_button(),
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                width="100%",
            ),
            rx.mobile_and_tablet(
                rx.hstack(
                    import_exercises_button(),
                    add_exercise_button(),
                ),
            ),
            rx.mobile_and_tablet(
                rx.hstack(
                    delete_selected_exercises_button(),
                    export_selected_exercises_button(),
                ),
            ),
            rx.mobile_and_tablet(
                edit_tags_button(),
            ),
            rx.mobile_and_tablet(
                search_bar(LectureManageExercisesState),
            ),
            rx.desktop_only(
                rx.hstack(
                    search_bar(LectureManageExercisesState),
                    edit_tags_button(),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                width="100%",
            ),
            search_badges(LectureManageExercisesState),
            exercise_table(),
            spacing="3",
            align="center",
            justify="center",
            width="100%",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
