"""The page to show the existing exercises."""

import reflex as rx

from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.exercises.components import render_exercises
from aitutor.pages.exercises.state import ExercisesState
from aitutor import routes


@with_navbar(routes.EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def exercises_page() -> rx.Component:
    """Default wrapper for exercises page"""
    return rx.container(
        rx.vstack(
            rx.heading("Exercises", size="8"),
            rx.hstack(
                rx.icon(tag="clock"),
                rx.moment(
                    format="HH:mm:ss",
                    interval=1000,
                    on_change=ExercisesState.update_time_left_strings,
                ),
            ),
            render_exercises(),
            spacing="5",
            justify="center",
            min_height="85vh",
            align="center",
        ),
    )
