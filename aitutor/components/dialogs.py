"""Dialog components for confirmation and destructive action dialogs.

This module provides reusable dialog components:
- confirm_dialog: customizable alert dialog with confirm/cancel actions
- confirm: non-destructive confirmation dialog
- destructive_confirm: destructive action confirmation dialog
"""

from typing import Union

import reflex as rx

TextLike = Union[str, rx.Var[str]]


def confirm_dialog(
    *,
    title: TextLike,
    description: TextLike,
    confirm_text: TextLike,
    cancel_text: TextLike,
    on_confirm,
    trigger: rx.Component,
    destructive: bool = False,
) -> rx.Component:
    """Create a reusable confirmation dialog component.

    This function generates an alert dialog that displays a title, description,
    and two actions: a primary "confirm" button and a secondary "cancel" button.
    It serves as the base implementation for both non-destructive (`confirm`)
    and destructive (`destructive_confirm`) dialog variants.

    Parameters
    ----------
    title : TextLike
        The dialog title. Can be a plain string or a reactive `rx.Var[str]`
        for dynamic updates.
    description : TextLike
        Additional explanatory text shown under the title. Also supports
        strings or reactive Vars.
    confirm_text : TextLike
        The label for the confirm button. Accepts plain or reactive text.
    cancel_text : TextLike
        The label for the cancel button. Accepts plain or reactive text.
    on_confirm : callable
        A callback function executed when the user clicks the confirm button.
    trigger : rx.Component
        A component that opens the dialog when interacted with (e.g. a button).
    destructive : bool, optional
        If True, the confirm button is styled as a destructive action (e.g. red).
        If False, the confirm button uses the standard primary color.

    Returns
    -------
    rx.Component
        A fully configured Reflex alert-dialog component."""

    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        rx.text(cancel_text),
                        _hover={"cursor": "pointer"},
                        variant=rx.cond(destructive, "solid", "outline"),
                    )
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.text(confirm_text),
                        color_scheme="red" if destructive else None,
                        on_click=on_confirm,
                        _hover={"cursor": "pointer"},
                    )
                ),
                margin_top="1em",
                justify="end",
            ),
        ),
    )


def confirm(
    *,
    title: TextLike,
    description: TextLike,
    confirm_text: TextLike,
    cancel_text: TextLike,
    on_confirm,
    trigger: rx.Component,
) -> rx.Component:
    """Create a confirmation dialog for safe, non-destructive actions.

    Use this dialog when asking the user to confirm an action that does not
    delete data or perform an irreversible change. This is a user-friendly
    wrapper around `confirm_dialog` with `destructive=False`.

    Parameters
    ----------
    title : TextLike
        The dialog title. Can be a plain string or a reactive `rx.Var[str]`
        for dynamic updates.
    description : TextLike
        A short explanation of the action the user is asked to confirm.
    confirm_text : TextLike
        The label for the primary confirm button.
    cancel_text : TextLike
        The label for the cancel button.
    on_confirm : callable
        A function executed when the user clicks the confirm button.
    trigger : rx.Component
        The UI element that opens the dialog when interacted with (e.g. a button).

    Returns
    -------
    rx.Component
        A configured non-destructive confirmation dialog.
    """
    return confirm_dialog(
        title=title,
        description=description,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        on_confirm=on_confirm,
        trigger=trigger,
        destructive=False,
    )


def destructive_confirm(
    *,
    title: TextLike,
    description: TextLike,
    confirm_text: TextLike,
    cancel_text: TextLike,
    on_confirm,
    trigger: rx.Component,
) -> rx.Component:
    """Create a confirmation dialog for destructive or irreversible actions.

    Use this dialog when confirming actions such as deleting data, removing
    items, or performing an operation that cannot be undone. This is a wrapper
    around `confirm_dialog` with `destructive=True`, which applies a more
    prominent (e.g. red) visual style to the confirm button.

    Parameters
    ----------
    title : TextLike
        The dialog title. Can be a plain string or a reactive `rx.Var[str]`
        for dynamic updates.
    description : TextLike
        A short explanation of the potentially destructive action.
    confirm_text : TextLike
        The label for the destructive confirm button.
    cancel_text : TextLike
        The label for the cancel button.
    on_confirm : callable
        A function executed when the user confirms.
    trigger : rx.Component
        The UI element that opens the dialog when interacted with (e.g. a button).

    Returns
    -------
    rx.Component
        A configured destructive confirmation dialog.
    """
    return confirm_dialog(
        title=title,
        description=description,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        on_confirm=on_confirm,
        trigger=trigger,
        destructive=True,
    )
