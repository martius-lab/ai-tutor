"""The email verification page."""

import reflex as rx

from aitutor.pages.navbar import with_navbar
from aitutor.pages.verify_email.components import verify_email_content


@with_navbar()
def verify_email_page() -> rx.Component:
    """Page that confirms an email address from the token in its route."""
    return rx.center(
        rx.card(verify_email_content()),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
