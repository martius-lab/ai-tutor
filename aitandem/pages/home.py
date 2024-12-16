"""This module contains the home page and related components."""


import reflex as rx
from aitandem.pages.sidebar import sidebar_default


@rx.page(route="/")
def home_default() -> rx.Component:
    """Render the homepage with sidebar."""
    return rx.hstack(
        sidebar_default(),  # Sidebar hinzufügen
        rx.container(
            rx.heading("Welcome to AI-Tandempartner", size="3"),
            rx.text("This is the main content area."),
            width="80%",  # Der Inhalt nimmt 80% der Breite ein
        ),
        spacing="4",  # Abstand zwischen den Komponenten
    )
