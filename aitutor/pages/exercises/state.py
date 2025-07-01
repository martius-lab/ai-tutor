"""State for the exercises page."""

import reflex as rx
import reflex_local_auth
from sqlmodel import and_, select
from typing import Optional

from aitutor.models import Exercise, ExerciseResult, UserRole
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_FORMAT


ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]


class ExercisesState(SessionState):
    """State for managing exercises."""

    has_exercises: bool = False
    has_tags: bool = False
    exercises_with_result: list[ExerciseWithResult] = []

    @rx.var
    def submit_time_stamps(self) -> dict[int, str]:
        """
        Dictionary to store submit time stamps for exercises.
        Key: Exercise ID, Value: Submit Time as string.
        """
        return {
            exercise_with_res[0].id: (
                exercise_with_res[1].submit_time_stamp.strftime(TIME_FORMAT)
                if exercise_with_res[1] is not None
                and exercise_with_res[1].submit_time_stamp is not None
                else ""
            )
            for exercise_with_res in self.exercises_with_result
            if exercise_with_res[0].id is not None
        }

    @rx.event
    def on_load(self):
        """
        Fetch exercises from database
        """
        # protect data against unauthorized access
        if not self.is_authenticated:
            return reflex_local_auth.LoginState.redir

        with rx.session() as session:
            stmt = select(Exercise, ExerciseResult).join(
                ExerciseResult,
                and_(
                    Exercise.id == ExerciseResult.exercise_id,
                    ExerciseResult.userinfo_id == self.authenticated_user.id,
                ),
                isouter=True,
            )
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TEACHER:
                stmt = stmt.where(Exercise.is_hidden == False)  # noqa: E712

            exercises_with_result = session.exec(stmt).all()
            self.has_exercises = len(exercises_with_result) > 0
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise, _ in exercises_with_result
            )
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.has_exercises = False
        self.has_tags = False
        self.exercises_with_result = []
