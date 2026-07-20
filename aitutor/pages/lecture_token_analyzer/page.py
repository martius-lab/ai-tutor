"""Lecture-specific token analyzer page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
from aitutor.pages.lecture_token_analyzer.components import (
    token_analyzer_exercise_analysis_section,
    token_analyzer_user_analysis_section,
    token_analyzer_view_menu,
)
from aitutor.pages.lecture_token_analyzer.state import (
    USER_ANALYSIS_VIEW,
    LectureTokenAnalyzerState,
)
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import (
    with_specific_lecture_navbar,
)


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "token_analyzer",
    LectureTokenAnalyzerState.current_lecture_id,
)
def lecture_token_analyzer_page() -> rx.Component:
    """Lecture-specific token analyzer page for token usage overview."""
    return rx.center(
        rx.vstack(
            token_analyzer_view_menu(),
            rx.cond(
                LectureTokenAnalyzerState.active_analysis_view == USER_ANALYSIS_VIEW,
                token_analyzer_user_analysis_section(),
                token_analyzer_exercise_analysis_section(),
            ),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
