"""State for the edit lecture page."""

import reflex as rx

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import GlobalPermission


class EditLectureState(SessionState):
    """State for the edit lecture page skeleton."""

    @rx.event
    @state_require_role_or_permission(
        allowed_permissions=[GlobalPermission.LECTURER],
    )
    def on_load(self):
        """Initialize the page state."""
        self.global_load()

    def on_logout(self):
        """Clear lecture-specific state on logout."""
