"""Displays the reported chat conversation in a lecture context."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.language_state import LanguageState
from aitutor.models import LectureRole
from aitutor.pages.chat.components import message_box
from aitutor.pages.lecture_report_view.state import LectureReportViewState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "reports",
    LectureReportViewState.current_lecture_id,
)
def lecture_report_view_page() -> rx.Component:
    """Renders the lecture-specific report view page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=20),
                        on_click=rx.redirect(LectureReportViewState.reports_route),
                        _hover={"cursor": "pointer"},
                    ),
                    rx.heading(LanguageState.report_detail, size="5"),
                    align="center",
                ),
                rx.hstack(
                    rx.cond(
                        ~LectureReportViewState.looked_at,
                        rx.icon("mail-check", size=18),
                        rx.icon("mail-open", size=18),
                    ),
                    rx.button(
                        rx.cond(
                            LectureReportViewState.looked_at,
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
                            LectureReportViewState.toggle_looked_at,
                            rx.redirect(LectureReportViewState.reports_route),
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
                        LectureReportViewState.exercise_title == None,
                        rx.text(LanguageState.deleted_report_title, color="red"),
                        rx.text(LectureReportViewState.exercise_title),
                    ),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("user-round", size=18),
                    rx.text(LanguageState.user + ":", weight="bold"),
                    rx.text(LectureReportViewState.username),
                    align="center",
                ),
                rx.hstack(
                    rx.icon("flag", size=18),
                    rx.text(LanguageState.report_message, weight="bold"),
                    align="center",
                ),
                rx.box(
                    rx.text(
                        LectureReportViewState.report_text,
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
                        LectureReportViewState.messages,
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
