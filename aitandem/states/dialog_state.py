"""Docstring."""

import reflex as rx


class DialogState(rx.State):
    """Docstring."""

    num_opens: int = 0
    opened: bool = False

    @rx.event
    def count_opens(self, value: bool):
        """Docstring."""
        self.opened = value
        self.num_opens += 1