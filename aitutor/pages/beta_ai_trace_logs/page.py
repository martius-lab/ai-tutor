"""Beta AI trace logs inspector page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import (
    page_require_lecture_role,
    page_require_role_or_permission,
)
from aitutor.models import LectureRole
from aitutor.pages.beta_ai_trace_logs.components import beta_ai_trace_logs_content
from aitutor.pages.beta_ai_trace_logs.state import BetaAITraceLogsState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


def trace_logs_content_page() -> rx.Component:
    """Render the shared inspector in either route."""
    return rx.center(
        beta_ai_trace_logs_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )


@page_require_role_or_permission()
@with_navbar(routes.BETA_AI_TRACE_LOGS)
def beta_ai_global_trace_logs_page() -> rx.Component:
    """Render traces across all lectures for global administrators."""
    return trace_logs_content_page()


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_beta_ai_navbar(
    routes.BETA_AI_TRACE_LOGS,
    BetaAITraceLogsState.current_lecture_id,
)
def beta_ai_trace_logs_page() -> rx.Component:
    """Render the Beta AI trace logs inspector page."""
    return trace_logs_content_page()
