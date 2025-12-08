"""Components for the Finished View page."""

import reflex as rx

from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState
from aitutor.pages.finished_view.state import FinishedViewState


def delete_submission_button() -> rx.Component:
    """
    Render the button to delete a submission.
    """
    return destructive_confirm(
        title=LanguageState.delete_submission,
        description=LanguageState.delete_submission_info,
        confirm_text=LanguageState.confirm,
        cancel_text=LanguageState.cancel,
        on_confirm=FinishedViewState.delete_submisssion,
        trigger=rx.button(
            LanguageState.delete_submission,
            color_scheme="red",
            _hover={"cursor": "pointer"},
        ),
    )
