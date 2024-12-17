"""This function displays a popup with a customizable error message.
Remember to import the file and the state"""


import reflex as rx
from aitandem.states.dialog_state import DialogState


def error_popup(trigger_component, description: str):
    """
    output: displays an error popup with the input message shown as a warning
    input: error message as a string (you can define it individually depending on
    what errr should be showing up), trigger event for the popup
    for example a button or link.
    Use it as follows:
    error_popup(
            rx.button("Open Error popup"),
            "This is a cool dialog description."
    )
    """
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