"""State for the Beta AI student exercise list."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, Lecture, LectureRole


class BetaAIStudentExercisesState(SessionState):
    """State for the student-facing Beta AI exercise entry page."""

    beta_exercises: list[BetaExercise] = []
    current_lecture_id: int | None = None

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def on_load(self):
        """Initialize the page and load visible Beta AI exercises."""
        self.global_load()
        self.current_lecture_id = None
        try:
            lecture_id = self.get_route_param_or_error("lecture_id", dtype=int)
        except Exception:
            return rx.redirect(routes.NOT_FOUND)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.load_beta_exercises()

    def on_logout(self):
        """Clear state on logout."""
        self.beta_exercises = []
        self.current_lecture_id = None

    @rx.event
    def load_beta_exercises(self):
        """Load Beta AI exercises that are visible to students."""
        if self.current_lecture_id is None:
            self.beta_exercises = []
            return
        with rx.session() as session:
            exercises = list(
                session.exec(
                    select(BetaExercise)
                    .where(
                        BetaExercise.lecture_id == self.current_lecture_id,
                        BetaExercise.is_hidden == False,  # noqa: E712
                    )
                    .order_by(BetaExercise.id.desc())  # type: ignore
                ).all()
            )

        self.beta_exercises = [
            exercise for exercise in exercises if exercise.is_started
        ]
