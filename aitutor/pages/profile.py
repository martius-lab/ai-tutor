"""Docstring."""

import reflex as rx

from aitutor.pages.login import require_login


@require_login()
def profile_default() -> rx.Component:
    """Profile page."""
    return rx.box()
