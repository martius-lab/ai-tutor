"""Tutor finished view for submitted Beta AI conversations."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.beta_ai_chat.components import chat_message
from aitutor.pages.beta_ai_finished_view_tutor.state import BetaAIFinishedViewTutorState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_SUBMISSIONS)
@page_require_role_at_least(UserRole.TUTOR)
def beta_ai_finished_view_tutor_page() -> rx.Component:
    """Render the tutor Beta AI finished view."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        on_click=rx.redirect(routes.BETA_AI_SUBMISSIONS),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading("Submitted Beta AI Chat", size="5"),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("book", size=18),
                    rx.text("Exercise:", weight="bold"),
                    rx.text(BetaAIFinishedViewTutorState.exercise_title),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("user-round", size=18),
                    rx.text("User:", weight="bold"),
                    rx.text(BetaAIFinishedViewTutorState.username),
                    align="center",
                ),
                rx.box(
                    rx.foreach(BetaAIFinishedViewTutorState.messages, chat_message),
                    overflow="auto",
                    width="100%",
                ),
                spacing="3",
                justify="start",
                min_height="82vh",
                max_height="82vh",
                height="100%",
                width="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
