"""Lecture edit/create page."""

import reflex as rx
import reflex_local_auth

from aitutor import routes
from aitutor.pages.edit_lecture.components import edit_lecture_content
from aitutor.pages.edit_lecture.state import EditLectureState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@reflex_local_auth.require_login
@with_navbar(routes.LECTURES)
def edit_lecture_page() -> rx.Component:
    """Lecture edit/create page."""
    content = rx.center(
        edit_lecture_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )

    return rx.cond(
        EditLectureState.is_new,
        content,
        with_specific_lecture_navbar(
            "settings",
            EditLectureState.current_lecture_id,
        )(lambda: content)(),
    )
