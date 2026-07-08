"""Beta AI student exercises page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_at_least
from aitutor.models import UserRole
from aitutor.pages.beta_ai_student_exercises.components import (
    beta_ai_student_exercises_content,
)
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar
from aitutor.language_state import LanguageState


def privacy_addendum() -> rx.Component:
    """Render the privacy addendum for the Beta AI student exercises page."""
    return rx.box(
        rx.markdown(LanguageState.beta_ai_privacy_addendum),
        bg=rx.color("accent", 3),
        padding_left="1em",
        padding_right="1em",
        width="100%",
    )


@with_navbar(routes.BETA_AI)
@with_beta_ai_navbar(routes.BETA_AI_STUDENT_EXERCISES)
@page_require_role_at_least(UserRole.STUDENT)
def beta_ai_student_exercises_page() -> rx.Component:
    """Render the Beta AI student exercises page."""
    return rx.center(
        rx.vstack(
            privacy_addendum(),
            beta_ai_student_exercises_content(),
            width="100%",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
   )
