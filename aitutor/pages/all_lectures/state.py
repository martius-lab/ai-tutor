"""State for the all lectures page."""

import reflex as rx

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import UserRole


class AllLecturesState(SessionState):
    """State scaffold for the all lectures page."""

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the page state."""
        self.global_load()