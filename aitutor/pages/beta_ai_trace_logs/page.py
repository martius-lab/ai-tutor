"""Beta AI trace logs inspector page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.beta_ai_trace_logs.components import beta_ai_trace_logs_content
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_TRACE_LOGS)
@page_require_role_at_least(UserRole.TUTOR)
def beta_ai_trace_logs_page() -> rx.Component:
    """Render the Beta AI trace logs inspector page."""
    return rx.center(
        beta_ai_trace_logs_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
