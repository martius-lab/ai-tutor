"""Page for tutor/admin Beta AI submissions."""

import reflex as rx

from aitutor import routes
from aitutor.beta_ai.legacy_page_protection import (
    legacy_beta_page_require_role_or_permission,
)
from aitutor.models import UserRole
from aitutor.pages.beta_ai_submissions.components import beta_ai_submissions_content
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_SUBMISSIONS)
@legacy_beta_page_require_role_or_permission(required_role=UserRole.TUTOR)
def beta_ai_submissions_page() -> rx.Component:
    """Render the Beta AI submissions page."""
    return rx.center(
        beta_ai_submissions_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
