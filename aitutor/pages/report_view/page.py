"""Displays the reported chat conversation."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.language_state import LanguageState
from aitutor.models import UserRole
from aitutor.pages.chat.components import message_box
from aitutor.pages.navbar import with_navbar
from aitutor.pages.report_view.state import ReportViewState


@with_navbar(routes.ADMIN_SETTINGS)
@page_require_role_or_permission(required_role=UserRole.TUTOR)
def report_view_page() -> rx.Component:
    """Renders the report view page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        on_click=rx.redirect(routes.REPORTS),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading(LanguageState.report_detail, size="5"),
                    align="center",
                ),
                rx.hstack(
                    rx.cond(
                        ~ReportViewState.looked_at,
                        rx.icon("mail-check", size=18),
                        rx.icon("mail-open", size=18),
                    ),
                    rx.button(
                        rx.cond(
                            ReportViewState.looked_at,
                            rx.hstack(
                                rx.text(LanguageState.report_mark_as_unread),
                                spacing="2",
                            ),
                            rx.hstack(
                                rx.text(LanguageState.report_mark_as_read),
                                spacing="2",
                            ),
                        ),
                        on_click=[
                            ReportViewState.toggle_looked_at,
                            rx.redirect(routes.REPORTS),
                        ],
                        _hover={"cursor": "pointer"},
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("book", size=18),
                    rx.text(LanguageState.exercise + ":", weight="bold"),
                    rx.cond(
                        ReportViewState.exercise_title == None,  # noqa: E711
                        rx.text(LanguageState.deleted_report_title, color="red"),
                        rx.text(ReportViewState.exercise_title),
                    ),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("user-round", size=18),
                    rx.text(LanguageState.user + ":", weight="bold"),
                    rx.text(ReportViewState.username),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("flag", size=18),
                    rx.text(LanguageState.report_message, weight="bold"),
                    align="center",
                ),
                rx.box(
                    rx.text(
                        ReportViewState.report_text,
                        padding="1em",
                        border_radius="8px",
                        background_color=rx.color("red", 3),
                        color=rx.color("red", 12),
                    ),
                    width="100%",
                ),
                rx.divider(),
                rx.text(
                    LanguageState.report_submitted_conversation, weight="bold", size="4"
                ),
                rx.box(
                    rx.foreach(
                        ReportViewState.messages,
                        message_box,
                    ),
                    width="100%",
                    padding_bottom="2em",
                ),
                spacing="3",
                justify="start",
                width="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
