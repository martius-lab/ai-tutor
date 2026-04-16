"""Lecture edit/create page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import GlobalPermission
from aitutor.pages.edit_lecture.components import edit_lecture_form
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_lectures import with_lectures_navbar


@with_navbar(routes.LECTURES)
@with_lectures_navbar(routes.EDIT_LECTURE + "/new")
@page_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
def edit_lecture_page() -> rx.Component:
    """Lecture edit/create page."""
    return rx.center(
        edit_lecture_form(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )