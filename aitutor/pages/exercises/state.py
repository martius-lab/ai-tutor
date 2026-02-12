"""State for the exercises page."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_FORMAT, TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, UserRole

ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]


class ExercisesState(SessionState):
    """State for managing exercises."""

    exercises_with_result: list[ExerciseWithResult] = []
    open_deadline_exercises: list[ExerciseWithResult] = []
    no_deadline_exercises: list[ExerciseWithResult] = []
    closed_deadline_exercises: list[ExerciseWithResult] = []
    time_left_strings: dict[int, str] = {}  # (exercise_id, time_left_string)

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """
        Fetch exercises from database
        """
        self.global_load()

        assert self.authenticated_user_info is not None
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
                        ExerciseResult.userinfo_id == self.authenticated_user_info.id,
                    ),
                    isouter=True,
                )
            )

            # Don't load hidden exercises for students
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TUTOR:
                stmt = stmt.where(Exercise.is_hidden == False)  # noqa: E712

            # fill self.exercises_with_result
            exercises_with_result = session.exec(
                stmt.order_by(func.lower(Exercise.title))
            ).all()
            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]

            # set not started exercises as hidden
            for exercise, _ in self.exercises_with_result:
                if not exercise.is_started:
                    exercise.is_hidden = True

            # if the user is a student, remove not started exercises
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TUTOR:
                self.exercises_with_result = [
                    ex_res
                    for ex_res in self.exercises_with_result
                    if not ex_res[0].is_hidden
                ]

            # fill open, closed and no deadline lists
            self.open_deadline_exercises = []
            self.no_deadline_exercises = []
            self.closed_deadline_exercises = []
            for ex_wth_res in self.exercises_with_result:
                exercise = ex_wth_res[0]
                if exercise.deadline_exceeded:
                    self.closed_deadline_exercises.append(ex_wth_res)
                elif exercise.deadline is None:
                    self.no_deadline_exercises.append(ex_wth_res)
                else:
                    self.open_deadline_exercises.append(ex_wth_res)

            # sort open_deadline_exercises by deadline ascending
            self.open_deadline_exercises.sort(
                key=lambda ex_wth_res: ex_wth_res[0].deadline
                if ex_wth_res[0].deadline is not None
                else datetime.max
            )

            # sort closed_deadline_exercises by deadline descending
            self.closed_deadline_exercises.sort(
                key=lambda ex_wth_res: ex_wth_res[0].deadline
                if ex_wth_res[0].deadline is not None
                else datetime.min,
                reverse=True,
            )

            # sort no_deadline_exercises by submitted vs not submitted
            self.no_deadline_exercises.sort(
                key=lambda ex_wth_res: ex_wth_res[1].submit_time_stamp is not None
                if ex_wth_res[1] is not None
                else False,
            )

            self.update_time_left_strings()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises_with_result = []
        self.open_deadline_exercises = []
        self.no_deadline_exercises = []
        self.closed_deadline_exercises = []
        self.time_left_strings = {}

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

    @rx.var
    def deadline_strings(self) -> dict[int, str]:
        """
        Dictionary to store deadline strings for exercises.
        Key: Exercise ID, Value: Deadline as string.
        """
        return {
            exercise.id: exercise.deadline.strftime("%d.%m.%Y, %H:%M")
            if exercise.deadline is not None
            else ""
            for exercise, _ in self.exercises_with_result
            if exercise.id is not None
        }

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
