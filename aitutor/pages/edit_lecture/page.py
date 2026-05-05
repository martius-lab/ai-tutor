"""Lecture edit/create page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import GlobalPermission
from aitutor.pages.edit_lecture.components import edit_lecture_content
from aitutor.pages.navbar import with_navbar


@with_navbar(routes.LECTURES)
@page_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
def edit_lecture_page() -> rx.Component:
    """Lecture edit/create page."""
    return rx.center(
        edit_lecture_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
