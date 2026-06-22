"""Lecture-specific prompts page."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_lecture_role
from aitutor.models import LectureRole
from aitutor.pages.lecture_prompts.components import lecture_prompt_management
from aitutor.pages.lecture_prompts.state import LectureManagePromptsState
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_specific_lecture import with_specific_lecture_navbar


@page_require_lecture_role(LectureRole.TUTOR)
@with_navbar(routes.LECTURES)
@with_specific_lecture_navbar(
    "manage_prompts",
    LectureManagePromptsState.current_lecture_id,
)
def lecture_prompts_page() -> rx.Component:
    """Manage prompts for one specific lecture."""
    return rx.center(
        lecture_prompt_management(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )