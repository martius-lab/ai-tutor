"""Displays the submitted chat messages for the tutor"""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import lecture_page_require_role_at_least
from aitutor.language_state import LanguageState
from aitutor.models import UserRole
from aitutor.pages.chat.components import message_box
from aitutor.pages.finished_view_tutor.state import FinishedViewTutorState
from aitutor.pages.navbar import with_navbar


@with_navbar(routes.SUBMISSIONS)
@lecture_page_require_role_at_least(UserRole.TUTOR)
def finished_view_tutor_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        on_click=rx.redirect(
                            routes.SUBMISSIONS,
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading(LanguageState.submitted_chat_tutor, size="5"),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("book", size=18),
                    rx.text(LanguageState.exercise + ":", weight="bold"),
                    rx.text(
                        FinishedViewTutorState.exercise_title,
                    ),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("user-round", size=18),
                    rx.text(LanguageState.user + ":", weight="bold"),
                    rx.text(
                        FinishedViewTutorState.username,
                    ),
                    align="center",
                ),
                rx.box(
                    rx.foreach(
                        FinishedViewTutorState.messages,
                        message_box,
                    ),
                    overflow="auto",
                    width="100%",
                ),
                spacing="3",
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
