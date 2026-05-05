"""Lecture overview page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.lecture_overview.components import lecture_overview_content
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar("lecture_overview")
@page_require_role_or_permission(required_role=UserRole.STUDENT)
def lecture_overview_page() -> rx.Component:
    """Show the lecture-specific overview page."""
    return rx.center(
        lecture_overview_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
