import reflex as rx
from aitandem.states.dialog_state import DialogState


def error_popup(trigger_component, description: str):
    return rx.dialog.root(
        rx.dialog.trigger(trigger_component),  # trigger element
        rx.dialog.content(
            rx.dialog.title("Error!"),  # error title
            rx.dialog.description(description),  # error description
            rx.dialog.close(
                rx.button("Close", size="3"),  # closing button
            ),
        ),
        on_open_change=DialogState.count_opens,  # changes the state
    )