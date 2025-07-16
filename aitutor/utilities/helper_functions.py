"""small functions to help"""

import reflex as rx


def truncate_text_reflex_var(text, max_length=100):
    """Truncate text to a maximum length with ellipsis."""
    return rx.cond(
        text.length() > max_length,
        text[:max_length] + "...",
        text,
    )
