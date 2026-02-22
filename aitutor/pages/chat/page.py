"""This module contains the chat component."""

import reflex as rx

import aitutor.routes as routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.language_state import LanguageState
from aitutor.models import UserRole
from aitutor.pages.chat.components import (
    chat_form,
    report_conversation_button,
    show_exercise_status,
    show_messages,
)
from aitutor.pages.chat.state import ChatState
from aitutor.pages.navbar import with_navbar


@with_navbar(routes.EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def chat_page() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            on_click=rx.redirect(routes.EXERCISES),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(
                            ChatState.exercise_title,
                            size="5",
                        ),
                        align="center",
                    ),
                    rx.tablet_and_desktop(
                        rx.hstack(
                            report_conversation_button(),
                            show_exercise_status(),
                            spacing="4",
                            align="center",
                        ),
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.mobile_only(
                    rx.hstack(
                        report_conversation_button(),
                        show_exercise_status(),
                        spacing="4",
                        align="center",
                    ),
                ),
                rx.cond(
                    ChatState.is_overdue,
                    rx.callout(
                        rx.box(
                           
                            rx.tablet_and_desktop(
                                LanguageState.cannot_submit_anymore_info,
                            ),
                            
                            rx.mobile_only(
                                "Deadline passed",
                            ),
                        ),
                        icon="info",
                        width="100%",
                        color_scheme="orange",
                        size="1",
                    ),
                ),
                # Show token warning when threshold reached (but not at limit)
                rx.cond(
                    ChatState.token_warning_threshold_reached & ~ChatState.token_limit_reached & ~ChatState.token_warning_callout_dismissed,
                    rx.hstack(
                        rx.callout(
                            rx.box(
                                rx.tablet_and_desktop(
                                    LanguageState.token_warning_message + f" {ChatState.token_usage_percentage}%.",
                                ),
                                rx.mobile_only(
                                    f"Token Warning: {ChatState.token_usage_percentage}% used",
                                ),
                            ),
                            icon="triangle-alert",
                            width="100%",
                            color_scheme="orange",
                            size="1",  
                        ),
                        rx.icon_button(
                            rx.icon("x", size=16),
                            on_click=ChatState.dismiss_token_warning_callout,
                            size="1",
                            variant="ghost",
                            color_scheme="orange",
                            _hover={"cursor": "pointer"},
                        ),
                        width="100%",
                        spacing="2",
                        align="center",
                    ),
                ),
                show_messages(),
                rx.cond(
                    ChatState.waiting_for_response,
                    rx.box(
                        rx.spinner(),
                    ),
                ),
                chat_form(),
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
