"""State for the exercises page."""

import reflex as rx
from sqlmodel import and_, select, desc
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from aitutor.models import Exercise, ExerciseResult, UserRole
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_FORMAT, TIME_ZONE
from aitutor.auth.protection import state_require_role_at_least


ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]


class ExercisesState(SessionState):
    """State for managing exercises."""

    exercises_with_result: list[ExerciseWithResult] = []
    open_deadline_ex: list[ExerciseWithResult] = []
    no_deadline_ex: list[ExerciseWithResult] = []
    closed_deadline_ex: list[ExerciseWithResult] = []
    deadline_strings: dict[int, str] = {}  # (exercise_id, deadline_string)
    time_left_strings: dict[int, str] = {}  # (exercise_id, time_left_string)

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

        self.global_load()
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
                stmt.order_by(desc(Exercise.deadline), Exercise.title)
            ).all()
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]
            # set not started exercises as hidden
            for exercise, _ in self.exercises_with_result:
                if not exercise.is_started:
                    exercise.is_hidden = True

            # if the user is a student, remove not started exercises
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TEACHER:
                self.exercises_with_result = [
                    ex_res
                    for ex_res in self.exercises_with_result
                    if not ex_res[0].is_hidden
                ]

            # fill open, closed and no deadline lists
            self.open_deadline_ex = []
            self.no_deadline_ex = []
            self.closed_deadline_ex = []
            for ex_wth_res in self.exercises_with_result:
                exercise = ex_wth_res[0]
                if exercise.deadline_exceeded:
                    self.closed_deadline_ex.append(ex_wth_res)
                elif exercise.deadline is None:
                    self.no_deadline_ex.append(ex_wth_res)
                else:
                    self.open_deadline_ex.append(ex_wth_res)

            self.update_time_left_strings()
            self.generate_deadline_strings()

    @rx.event
    def update_time_left_strings(self):
        """get the datetime time left for every exercise"""
        for exercise, _ in self.exercises_with_result:
            if exercise.deadline:
                deadline = exercise.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
                time_left = deadline - datetime.now(ZoneInfo(TIME_ZONE))
                if time_left.total_seconds() <= 0:
                    self.time_left_strings[exercise.id] = ""  # type: ignore
                else:
                    days = time_left.days
                    hours, remainder = divmod(time_left.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    self.time_left_strings[exercise.id] = f"{days}d {hours}h {minutes}m"  # type: ignore

    def generate_deadline_strings(self):
        """Get the deadline string for every exercise."""
        for exercise, _ in self.exercises_with_result:
            if exercise.deadline:
                self.deadline_strings[exercise.id] = exercise.deadline.strftime(  # type: ignore
                    "%d.%m.%Y, %H:%M"
                )
            else:
                self.deadline_strings[exercise.id] = ""  # type: ignore

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises_with_result = []
        self.open_deadline_ex = []
        self.no_deadline_ex = []
        self.closed_deadline_ex = []
        self.deadline_strings = {}
        self.time_left_strings = {}
