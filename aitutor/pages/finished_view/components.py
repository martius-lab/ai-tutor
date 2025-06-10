"""Components for the Finished View page."""

import reflex as rx

from aitutor.pages.finished_view.state import FinishedViewState


def delete_submission_button() -> rx.Component:
    """
    Render the button to reset the conversation.
    """
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                "Delete Submission",
                color_scheme="red",
                _hover={"cursor": "pointer"},
            )
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Submission"),
            rx.alert_dialog.description(
                "Are you sure you want to delete your submision?"
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        color_scheme="red",
                        _hover={"cursor": "pointer"},
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirm",
                        color_scheme="iris",
                        _hover={"cursor": "pointer"},
                        on_click=FinishedViewState.delete_submisssion,
                    ),
                ),
                margin_top="1em",
            ),
        ),
    )
