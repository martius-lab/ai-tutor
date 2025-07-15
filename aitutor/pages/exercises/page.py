"""The page to show the existing exercises."""

import reflex as rx

from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.exercises.components import render_exercises


@with_navbar
@page_require_role_at_least(UserRole.STUDENT)
def exercises_page() -> rx.Component:
    """Default wrapper for exercises page"""
    return rx.container(
        rx.vstack(
            rx.heading("Exercises", size="8"),
            render_exercises(),
            spacing="5",
            justify="center",
            min_height="85vh",
            align="center",
        ),
    )
