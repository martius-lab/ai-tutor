"""Displays the submitted chat messages for the teacher"""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.finished_view_teacher.state import FinishedViewTeacherState
from aitutor import routes
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.chat.components import message_box


@with_navbar(routes.SUBMISSIONS)
@page_require_role_at_least(UserRole.TEACHER)
def finished_view_teacher_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        color_scheme="iris",
                        on_click=rx.redirect(
                            routes.SUBMISSIONS,
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading(
                        f"Submitted by {FinishedViewTeacherState.username} "
                        f"for exercise: {FinishedViewTeacherState.exercise_title}",
                        size="5",
                    ),
                    align="center",
                ),
                rx.box(
                    rx.foreach(
                        FinishedViewTeacherState.messages,
                        message_box,
                    ),
                    overflow="auto",
                    width="100%",
                ),
                spacing="5",
                justify="start",
                min_height="85vh",
                max_height="85vh",
                height="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
