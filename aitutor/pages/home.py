"""This module contains the home page and related components."""

import reflex as rx
from aitutor.pages.navbar import with_navbar


@rx.page(route="/")
@with_navbar
def home_default() -> rx.Component:
    """Render the homepage with sidebar."""
    return rx.container(
        rx.color_mode.button(position="bottom-left", type="button"),
        rx.heading("Welcome to AI-Tandempartner", size="3"),
        rx.text("This is the main content area."),
        width="80%",
        center_content=True,
        align_items="center",
    )
