"""My lectures page."""

import reflex as rx
import reflex_local_auth

from aitutor import routes
from aitutor.pages.my_lectures.components import my_lectures_content
from aitutor.pages.navbar import with_navbar


@reflex_local_auth.require_login
@with_navbar(routes.LECTURES)
def my_lectures_page() -> rx.Component:
    """Show the lectures visible to the current user."""
    return rx.center(
        my_lectures_content(),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
