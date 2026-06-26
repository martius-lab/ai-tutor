"""Student finished view for submitted Beta AI conversations."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.beta_ai_chat.components import chat_message
from aitutor.pages.beta_ai_finished_view.state import BetaAIFinishedViewState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_STUDENT_EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def beta_ai_finished_view_page() -> rx.Component:
    """Render the student Beta AI finished view."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        on_click=rx.redirect(BetaAIFinishedViewState.chat_url),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.icon("circle-check", color=gv.GREEN_CHECK_COLOR),
                    rx.heading("Submitted Beta AI Chat", size="5"),
                    rx.tablet_and_desktop(
                        rx.text(
                            BetaAIFinishedViewState.exercise_title,
                            weight="bold",
                            size="3",
                        ),
                    ),
                    align="center",
                ),
                rx.mobile_only(
                    rx.text(
                        BetaAIFinishedViewState.exercise_title,
                        weight="bold",
                        size="3",
                    ),
                ),
                rx.box(
                    rx.foreach(BetaAIFinishedViewState.messages, chat_message),
                    overflow="auto",
                    width="100%",
                ),
                spacing="5",
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
