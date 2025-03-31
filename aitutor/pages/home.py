"""This module contains the home page and related components."""

import reflex as rx
from aitutor.pages.sidebar import with_sidebar


@rx.page(route="/")
@with_sidebar
def home_default() -> rx.Component:
    """Render the homepage with sidebar."""
    return rx.container(
        rx.heading("Welcome to AI-Tandempartner", size="3"),
        rx.text("This is the main content area."),
        width="80%",
    )
