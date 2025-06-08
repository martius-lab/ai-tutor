"""404 - Page Not Found component for the application."""

import reflex as rx
from aitutor.routes import HOME


def not_found_page():
    """Render the 404 - Page Not Found component."""
    return rx.center(
        rx.vstack(
            rx.text("404 - Page Not Found", font_size="2xl", color="red"),
            rx.link("Go Home", href=HOME),
            align_items="center",
        ),
        height="100vh",
        width="100vw",
    )
