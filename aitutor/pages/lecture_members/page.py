"""Lecture members page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.lecture_members.components import lecture_members_content
from aitutor.pages.lecture_members.state import LectureMembersState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@page_require_role_or_permission(required_role=UserRole.STUDENT)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "members",
    LectureMembersState.current_lecture_id,
)
def lecture_members_page() -> rx.Component:
    """Show the lecture-specific members page."""
    return rx.center(
        lecture_members_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
