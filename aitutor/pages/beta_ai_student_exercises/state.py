"""State for the Beta AI student exercise list."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, UserRole


class BetaAIStudentExercisesState(SessionState):
    """State for the student-facing Beta AI exercise entry page."""

    beta_exercises: list[BetaExercise] = []

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """Initialize the page and load visible Beta AI exercises."""
        self.global_load()
        self.load_beta_exercises()

    def on_logout(self):
        """Clear state on logout."""
        self.beta_exercises = []

    @rx.event
    def load_beta_exercises(self):
        """Load Beta AI exercises that are visible to students."""
        with rx.session() as session:
            exercises = list(
                session.exec(
                    select(BetaExercise)
                    .where(BetaExercise.is_hidden == False)  # noqa: E712
                    .order_by(BetaExercise.id.desc())  # type: ignore
                ).all()
            )

        self.beta_exercises = [
            exercise for exercise in exercises if exercise.is_started
        ]
