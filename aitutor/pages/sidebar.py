"""This module contains the sidebar component and its links."""

import reflex as rx

# Gemeinsame Style-Definition für die Links
LINK_STYLE = rx.Style(font_size="16px", margin="10px", color="#007bff")


def create_link(text: str, href: str) -> rx.Component:
    """Helper function to create styled links."""
    return rx.link(
        text,
        href=href,
        style=LINK_STYLE,
    )


def sidebar_default() -> rx.Component:
    """Render the sidebar component with links, styled to match registration page."""
    return rx.box(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.heading(
                        "AI-Tandempartner",  # Titel in der Sidebar
                        size="4",
                        as_="h4",
                        text_align="center",
                        color="#343a40",
                    ),
                    direction="column",
                    spacing="5",
                    width="100%",
                ),
                # Sidebar Links
                create_link("Home", "/"),
                create_link("Login", "/login"),
                create_link("Registration", "/register"),
                create_link("Chat", "/chat"),
                create_link("Add Exercises", "/add-exercises"),
                create_link("Exercises", "/exercises"),
                direction="column",  # Links vertikal
                align_items="flex-start",  # Links linksbündig
                width="100%",
            ),
            max_width="15em",  # Sidebar Breite
            size="4",
            width="100%",
            border_radius="10px",  # Abgerundete Ecken
            box_shadow="0px 4px 8px rgba(0, 0, 0, 0.1)",  # Schatten
        ),
        padding="1rem",  # Padding für die Sidebar
        background_color="#f8f9fa",  # Heller Hintergrund
        height="100vh",  # Sidebar soll ganze Höhe einnehmen
    )


def with_sidebar(
    component_factory: rx.app.ComponentCallable,
) -> rx.app.ComponentCallable:
    """Decorator to add navigation sidebar to a component."""
    return lambda: rx.hstack(
        sidebar_default(),
        component_factory(),
        spacing="4",
    )
