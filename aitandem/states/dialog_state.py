import reflex as rx
from aitandem.states.dialog_state import DialogState


def error_popup(trigger_component, description: str):
    return rx.dialog.root(
        rx.dialog.trigger(trigger_component),
        rx.dialog.content(
            rx.dialog.title("Error!"),
            rx.dialog.description(description),
            rx.dialog.close(
                rx.button("Close", size="3"),
            ),
        ),
        on_open_change=DialogState.count_opens,
    )