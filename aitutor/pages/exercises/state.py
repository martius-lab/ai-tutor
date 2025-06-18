"""State for the exercises page."""

import reflex as rx
from sqlmodel import select
from typing import Optional

from aitutor.models import Exercise
from aitutor.models import ExerciseResult
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
        with rx.session() as session:
            stmt = select(Exercise, ExerciseResult).join(ExerciseResult, isouter=True)
            exercises_with_result = session.exec(stmt).all()
            self.has_exercises = len(exercises_with_result) > 0
            self.has_tags = any(
                len(exercise.tags) > 0 for exercise, _ in exercises_with_result
            )
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]
