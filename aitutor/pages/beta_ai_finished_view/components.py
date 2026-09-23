"""Components for the student Better AI finished view."""

import reflex as rx

from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState
from aitutor.pages.beta_ai_finished_view.state import BetaAIFinishedViewState


def delete_submission_button() -> rx.Component:
    """Render the confirmation button for withdrawing a Better AI submission."""
    return destructive_confirm(
        title=LanguageState.delete_submission,
        description=LanguageState.delete_submission_info,
        confirm_text=LanguageState.confirm,
        cancel_text=LanguageState.cancel,
        on_confirm=BetaAIFinishedViewState.delete_submission,
        trigger=rx.button(
            LanguageState.delete_submission,
            color_scheme="red",
            _hover={"cursor": "pointer"},
        ),
    )