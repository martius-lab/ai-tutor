"""Components for the Finished View page."""

import reflex as rx

from aitutor.language_state import LanguageState
from aitutor.pages.finished_view.state import FinishedViewState


def delete_submission_button() -> rx.Component:
    """
    Render the button to reset the conversation.
    """
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                LanguageState.delete_submission,
                color_scheme="red",
                _hover={"cursor": "pointer"},
            )
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title(LanguageState.delete_submission),
            rx.alert_dialog.description(LanguageState.delete_submission_info),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        rx.text(LanguageState.cancel),
                        color_scheme="red",
                        _hover={"cursor": "pointer"},
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LanguageState.confirm,
                        color_scheme="iris",
                        _hover={"cursor": "pointer"},
                        on_click=FinishedViewState.delete_submisssion,
                    ),
                ),
                margin_top="1em",
            ),
        ),
    )
