"""Lecture edit/create page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.edit_lecture.components import edit_lecture_content
from aitutor.pages.edit_lecture.state import EditLectureState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@page_require_role_or_permission(required_role=UserRole.STUDENT)
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
