"""Token Analyzer page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar
from aitutor.pages.token_analyzer.components import (
    token_analyzer_exercise_analysis_section,
    token_analyzer_user_analysis_section,
    token_analyzer_view_menu,
)
from aitutor.pages.token_analyzer.state import (
    TokenAnalyzerState,
    USER_ANALYSIS_VIEW,
)


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.TOKEN_ANALYZER)
@page_require_role_at_least(UserRole.ADMIN)
def token_analyzer_page() -> rx.Component:
    """Token analyzer page for user token usage overview."""
    return rx.center(
        rx.vstack(
            token_analyzer_view_menu(),
            rx.cond(
                TokenAnalyzerState.active_analysis_view == USER_ANALYSIS_VIEW,
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
