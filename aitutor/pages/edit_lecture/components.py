"""Components for the edit lecture page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS


def edit_lecture_placeholder() -> rx.Component:
    """Temporary placeholder for the lecture editor."""
    return rx.card(
        rx.vstack(
            rx.heading(LS.edit_lecture, size="6"),
            rx.text(LS.edit_lecture_placeholder),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="40em",
        max_width="90vw",
        variant="ghost",
    )