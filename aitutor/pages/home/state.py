"""The state for the home page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.state import SessionState
from aitutor.models import Exercise, UserRole
from aitutor.auth.protection import state_require_role_at_least


class HomeState(SessionState):
    """The state for the home page."""

    exercises: list[Exercise] = []

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """Load exercises when the home page is loaded."""
        with rx.session() as session:
            exercises = session.exec(select(Exercise)).all()
            self.exercises = list(exercises)

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises = []
