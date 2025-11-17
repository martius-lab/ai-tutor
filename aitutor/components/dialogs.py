"""Dialog components for confirmation and destructive action dialogs.

This module provides reusable dialog components:
- confirm_dialog: customizable alert dialog with confirm/cancel actions
- confirm: non-destructive confirmation dialog
- destructive_confirm: destructive action confirmation dialog
"""

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
    """refactoring alert_dialog with destructive and non-destructive versions"""

    confirm_color = "red" if destructive else "iris"
    cancel_color = "iris" if destructive else "red"

    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        rx.text(cancel_text),
                        color_scheme=cancel_color,
                        _hover={"cursor": "pointer"},
                    )
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.text(confirm_text),
                        color_scheme=confirm_color,
                        on_click=on_confirm,
                        _hover={"cursor": "pointer"},
                    )
                ),
                margin_top="1em",
            ),
        ),
    )


def confirm(**props):
    """Create a non-destructive confirmation dialog.

    Parameters
    ----------
    **props
        Properties to pass to confirm_dialog, including title, description,
        confirm_text, cancel_text, on_confirm, and trigger.

    Returns
    -------
    rx.Component
        A confirmation dialog component.
    """
    return confirm_dialog(**props, destructive=False)


def destructive_confirm(**props):
    """Create a destructive action confirmation dialog.

    Parameters
    ----------
    **props
        Properties to pass to confirm_dialog, including title, description,
        confirm_text, cancel_text, on_confirm, and trigger.

    Returns
    -------
    rx.Component
        A destructive confirmation dialog component.
    """
    return confirm_dialog(**props, destructive=True)
