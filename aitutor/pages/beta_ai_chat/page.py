"""Beta AI chat skeleton page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.language_state import LanguageState
from aitutor.models import UserRole
from aitutor.pages.beta_ai_chat.components import (
    analysis_preference,
    beta_submission_status,
    message_input,
    messages_panel,
    report_conversation_button,
)
from aitutor.pages.beta_ai_chat.state import BetaAIChatState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@page_require_role_or_permission(required_role=UserRole.STUDENT)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "exercises",
    BetaAIChatState.current_lecture_id,
)
def beta_ai_chat_page() -> rx.Component:
    """Render the Beta AI chat page with the student chat layout."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            on_click=rx.redirect(BetaAIChatState.exercises_url),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(BetaAIChatState.exercise_title, size="5"),
                        align="center",
                    ),
                    rx.tablet_and_desktop(
                        rx.hstack(
                            report_conversation_button(),
                            beta_submission_status(),
                            spacing="4",
                            align="center",
                        )
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.mobile_only(
                    rx.hstack(
                        report_conversation_button(),
                        beta_submission_status(),
                        spacing="4",
                        align="center",
                    )
                ),
                rx.cond(
                    BetaAIChatState.is_overdue,
                    rx.callout(
                        rx.box(
                            rx.tablet_and_desktop(
                                LanguageState.cannot_submit_anymore_info,
                            ),
                            rx.mobile_only(
                                LanguageState.cannot_submit_anymore_info_mobile,
                            ),
                        ),
                        icon="info",
                        width="100%",
                        color_scheme="orange",
                        size="1",
                        variant="surface",
                    ),
                ),
                rx.tablet_and_desktop(
                    rx.cond(
                        BetaAIChatState.token_warning_threshold_reached
                        & ~BetaAIChatState.token_limit_reached,
                        rx.callout(
                            rx.box(
                                LanguageState.token_warning_message
                                + f" {BetaAIChatState.token_usage_percentage}%."
                            ),
                            icon="triangle-alert",
                            width="100%",
                            color_scheme="orange",
                            size="1",
                            variant="surface",
                        ),
                    ),
                    width="100%",
                ),
                rx.mobile_only(
                    rx.cond(
                        BetaAIChatState.token_warning_threshold_reached
                        & ~BetaAIChatState.token_limit_reached,
                        rx.callout(
                            rx.box(
                                LanguageState.token_warning_message_mobile
                                + f" {BetaAIChatState.token_usage_percentage}%."
                            ),
                            icon="triangle-alert",
                            width="100%",
                            color_scheme="orange",
                            size="1",
                            variant="surface",
                        ),
                    ),
                    width="100%",
                ),
                messages_panel(),
                rx.cond(
                    BetaAIChatState.running_diagnosis,
                    rx.box(rx.spinner()),
                ),
                message_input(),
                analysis_preference(),
                spacing="3",
                justify="start",
                width="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
