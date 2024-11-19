<<<<<<< HEAD
"""Docstring."""

import reflex as rx


def settings_default() -> rx.Component:
    """Settings page."""
    return rx.box()
=======
import reflex as rx
from ..components.sidebar import sidebar_default


def settings_default() -> rx.Component:
    return rx.hstack(
        sidebar_default(),
        rx.container(
            rx.color_mode.button(position="top-right"),
            rx.vstack(
                rx.heading("Change your Settings!", size="9"),
                rx.text(
                    "Choose your language and start learning! ",
                    size="5",
                ),
                spacing="5",
                justify="center",
                min_height="85vh",
            ),
            rx.logo(),
        ),
    )
>>>>>>> 5cca67505bdf79f2281212a51cbf46a105bc82b0
