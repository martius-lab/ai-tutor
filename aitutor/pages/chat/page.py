"""This module contains the chat component."""

import reflex as rx

import aitutor.routes as routes
from aitutor.models import UserRole
from aitutor.pages.chat.state import ChatState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.pages.chat.components import show_messages, chat_form, show_exercise_status


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def chat_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            color_scheme="iris",
                            on_click=rx.redirect(routes.EXERCISES),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(
                            "Exercise: " + ChatState.exercise_title,
                            size="5",
                        ),
                        align="center",
                    ),
                    show_exercise_status(),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                show_messages(),
                chat_form(),
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
