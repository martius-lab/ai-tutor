"""Collection of components that are used on multiple pages."""

import reflex as rx
from .dialogs import confirm_dialog, confirm, destructive_confirm


class PasswordInput(rx.ComponentState):
    """A password input component with show/hide toggle."""

    password_visible: bool = False

    @rx.event
    def toggle_password_visibility(self):
        """Toggle the visibility of the password."""
        self.password_visible = not self.password_visible

    @rx.event
    def hide_password(self):
        """Hide the password."""
        self.password_visible = False

    @classmethod
    def get_component(cls, **props):
        """Create the component."""
        return rx.hstack(
            rx.input(
                type=rx.cond(cls.password_visible, "text", "password"),
                on_mount=cls.hide_password,
                **props,
            ),
            rx.icon(
                rx.cond(cls.password_visible, "eye", "eye-off"),
                on_click=cls.toggle_password_visibility,
                _hover={"cursor": "pointer"},
            ),
            align="center",
            width="100%",
        )


password_input = PasswordInput.create
