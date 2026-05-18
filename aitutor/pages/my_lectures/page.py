"""My lectures page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import UserRole
from aitutor.pages.my_lectures.components import my_lectures_content
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_lectures import with_lectures_navbar


@with_navbar(routes.LECTURES)
@with_lectures_navbar(routes.MY_LECTURES)
@page_require_role_or_permission(required_role=UserRole.STUDENT)
def my_lectures_page() -> rx.Component:
    """Show the lectures visible to the current user."""
    return rx.center(
        my_lectures_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
