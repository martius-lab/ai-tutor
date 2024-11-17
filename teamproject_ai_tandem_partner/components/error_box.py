import reflex as rx

#displays an error popup with the input message shown as a warning
#input: error message (you can define it individually depending on what errr should be showing up)
def error_popup(message: str):
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header("Error"), #popup title
                rx.modal_body(rx.text(message, color="red")), #display the error message in red
                rx.modal_footer(
                    rx.button("Close", on_click=rx.close_modal) #closes popup
                ),
            )
        ),
        is_open=True, #make the popup visible
    )
