"""The state for the configuration page."""

import reflex as rx
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least
from aitutor.models import UserRole


class ConfigurationState(SessionState):
    """The State for the configuration page."""

    config_dialog_open: bool = False

    @rx.event
    def set_config_dialog_open(self, is_open: bool):
        """Sets whether the config dialog is open."""
        self.config_dialog_open = is_open

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        self.global_load()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.config_dialog_open = False
