"""Page add/edit exercises."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
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
from aitutor.search.components import search_badges, search_bar


@page_require_lecture_role(LectureRole.OWNER)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "manage_exercises",
    LectureManageExercisesState.current_lecture_id,
)
def lecture_manage_exercises_page() -> rx.Component:
    """Manage lecture-specific exercises page."""
    return rx.center(
        rx.vstack(
            _toolbar(),
            rx.box(edit_tags_button(), align_self="center"),
            search_bar(LectureManageExercisesState),
            search_badges(LectureManageExercisesState),
            exercise_table(),
            spacing="6",
            width="100%",
        ),
        margin_y="2em",
        width="100%",
    )


def _toolbar() -> rx.Component:
    """Selection actions left, lecture actions right; wraps on small screens."""
    return rx.hstack(
        rx.hstack(
            delete_selected_exercises_button(),
            export_selected_exercises_button(),
        ),
        rx.hstack(
            import_exercises_button(),
            add_exercise_button(),
        ),
        justify="between",
        wrap="wrap",
        width="100%",
    )
