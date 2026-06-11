"""Password reset pages."""

import reflex as rx

from aitutor.pages.account_emails.components import (
    forgot_password_form,
    reset_password_form,
)
from aitutor.pages.navbar import with_navbar


@with_navbar()
def forgot_password_page() -> rx.Component:
    """Password reset request page."""
    return rx.center(
        rx.card(forgot_password_form()),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )


@with_navbar()
def reset_password_page() -> rx.Component:
    """Password reset page."""
    return rx.center(
        rx.card(reset_password_form()),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
