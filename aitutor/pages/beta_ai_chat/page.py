"""Beta AI chat skeleton page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.beta_ai_chat.components import (
    beta_submission_status,
    message_input,
    messages_panel,
)
from aitutor.pages.beta_ai_chat.state import BetaAIChatState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_STUDENT_EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def beta_ai_chat_page() -> rx.Component:
    """Render the Beta AI chat page with the student chat layout."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            on_click=rx.redirect(routes.BETA_AI_STUDENT_EXERCISES),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(BetaAIChatState.exercise_title, size="5"),
                        align="center",
                    ),
                    rx.tablet_and_desktop(beta_submission_status()),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.mobile_only(beta_submission_status()),
                messages_panel(),
                rx.cond(
                    BetaAIChatState.running_diagnosis,
                    rx.box(rx.spinner()),
                ),
                message_input(),
                spacing="3",
                justify="start",
                width="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
