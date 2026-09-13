"""Beta AI diagnosis lab page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
from aitutor.pages.beta_ai_diagnosis_lab.components import (
    beta_ai_diagnosis_lab_content,
)
from aitutor.pages.beta_ai_diagnosis_lab.state import BetaAIDiagnosisLabState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_beta_ai import with_beta_ai_navbar


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_beta_ai_navbar(
    routes.BETA_AI_DIAGNOSIS_LAB,
    BetaAIDiagnosisLabState.current_lecture_id,
)
def beta_ai_diagnosis_lab_page() -> rx.Component:
    """Render the Beta AI diagnosis lab page."""
    return rx.center(
        beta_ai_diagnosis_lab_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
