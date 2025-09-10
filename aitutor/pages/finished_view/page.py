"""Displays the submitted chat messages"""

import reflex as rx

from aitutor.models import UserRole
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.chat.components import message_box
from aitutor.pages.finished_view.components import delete_submission_button
from aitutor import routes


@with_navbar(routes.EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def finished_view_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        color_scheme="iris",
                        on_click=rx.redirect(
                            FinishedViewState.chat_url,
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading(
                        "Your submission for exercise: "
                        + FinishedViewState.exercise_title,
                        size="5",
                    ),
                    align="center",
                ),
                rx.box(
                    rx.foreach(
                        FinishedViewState.messages,
                        message_box,
                    ),
                    overflow="auto",
                    width="100%",
                ),
                delete_submission_button(),
                spacing="5",
                justify="start",
                min_height="82vh",
                max_height="82vh",
                height="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
