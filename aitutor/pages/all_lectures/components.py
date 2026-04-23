"""Components for the all lectures page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS


def all_lectures_content() -> rx.Component:
    """Initial scaffold content for the all lectures page."""
    return rx.vstack(
        rx.heading(LS.all_lectures, size="6"),
        rx.text(
            "test1",
            text_align="center",
        ),
        spacing="3",
        align="center",
        width="100%",
    )