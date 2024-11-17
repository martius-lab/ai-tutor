import reflex as rx

"""
output: displays an error popup with the input message shown as a warning
input: error message as a string (you can define it individually depending on what errr should be showing up)

use it as
     example_popup = error_popup("Error 404")
     if event_trigger:
         show example_popup
"""


def error_popup(message: str):
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header("Error"),  # popup title
                rx.modal_body(
                    rx.text(message, color="red")
                ),  # display the error message in red
                rx.modal_footer(
                    rx.button(
                        "Close", on_click=rx.close_modal
                    )  # closes popup when clicking on "close"
                ),
            )
        ),
        is_open=True,  # make the popup visible
    )
