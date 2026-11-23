"""Form-related UI components."""

import reflex as rx


def form_label(text: str | rx.vars.StringVar[str]) -> rx.Component:
    """Create a form label."""
    return rx.text(
        text,
        size="3",
        weight="medium",
        text_align="left",
        width="100%",
        padding_top="1.5em",
        padding_bottom="0.5em",
    )
