"""Beta AI exercises page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import GlobalPermission
from aitutor.pages.beta_ai_exercises.components import beta_ai_exercises_content
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_EXERCISES)
@page_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
def beta_ai_exercises_page() -> rx.Component:
    """Render the Beta AI exercises page."""
    return rx.center(
        beta_ai_exercises_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
