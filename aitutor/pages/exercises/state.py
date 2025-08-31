"""State for the exercises page."""

import reflex as rx
from sqlmodel import and_, select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aitutor.models import Exercise, ExerciseResult, UserRole
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_FORMAT, TIME_ZONE
from aitutor.auth.protection import state_require_role_at_least


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
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """
        Fetch exercises from database
        """

        with rx.session() as session:
            stmt = (
                select(Exercise, ExerciseResult)
                .options(
                    selectinload(Exercise.tags),  # type: ignore
                )
                .join(
                    ExerciseResult,
                    and_(
                        Exercise.id == ExerciseResult.exercise_id,
                        ExerciseResult.userinfo_id == self.authenticated_user.id,
                    ),
                    isouter=True,
                )
            )
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TEACHER:
                stmt = stmt.where(Exercise.is_hidden == False)  # noqa: E712

            exercises_with_result = session.exec(
                stmt.order_by(Exercise.id.desc())  # type: ignore
            ).all()
            self.has_exercises = len(exercises_with_result) > 0
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise, _ in exercises_with_result
            )
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]
            self.hide_not_started_exercises()

    def hide_not_started_exercises(self):
        """Hide exercises that have not started yet."""
        for exercise_with_res in self.exercises_with_result:
            exercise = exercise_with_res[0]
            if exercise.deadline and exercise.days_to_complete:
                end = datetime.strptime(exercise.deadline, "%Y-%m-%dT%H:%M").replace(
                    tzinfo=ZoneInfo(TIME_ZONE)
                )
                start = end - timedelta(days=exercise.days_to_complete)
                current_time = datetime.now(ZoneInfo(TIME_ZONE))
                if current_time < start:
                    exercise.is_hidden = True

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.has_exercises = False
        self.has_tags = False
        self.exercises_with_result = []
