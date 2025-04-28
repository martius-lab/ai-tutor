"""This module contains the home page and related components."""

import reflex as rx
from aitutor.pages.navbar import with_navbar
from ..auth.state import SessionState


@rx.page(route="/")
@with_navbar
def home_default() -> rx.Component:
    """Render the homepage with navbar."""
    username = SessionState.authenticated_user.username
    return rx.container(
        rx.flex(
            rx.cond(
                SessionState.is_authenticated,
                rx.heading(f"Welcome back, {username}!", size="7"),
                rx.heading("You are not logged in.", size="7"),
            ),
            align="center",
            justify="center",
            height="85vh",
            width="100%",
        )
    )
