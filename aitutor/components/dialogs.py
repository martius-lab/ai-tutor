import reflex as rx

def confirm_dialog(
    title: str,
    description: str,
    confirm_text: str,
    cancel_text: str,
    on_confirm,
    trigger: rx.Component,
    destructive: bool = False,
) -> rx.Component:
    """Wiederverwendbarer Confirm Dialog."""

    confirm_color = "red" if destructive else "iris"
    cancel_color = "iris" if destructive else "red"

    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(cancel_text, color_scheme=cancel_color)
                ),
                rx.alert_dialog.action(
                    rx.button(
                        confirm_text,
                        color_scheme=confirm_color,
                        on_click=on_confirm,
                    )
                ),
                margin_top="1em",
            ),
        ),
    )


def confirm(**props):
    return confirm_dialog(**props, destructive=False)


def destructive_confirm(**props):
    return confirm_dialog(**props, destructive=True)
