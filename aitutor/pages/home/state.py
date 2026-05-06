"""The state for the home page."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import and_, or_, select

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, UserRole


class HomeState(SessionState):
    """The state for the home page."""

    exercises_with_result: list[tuple[Exercise, Optional[ExerciseResult]]] = []

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load exercises when the home page is loaded."""
        self.global_load()

        assert self.authenticated_user_info is not None
        with rx.session() as session:
            stmt = (
                select(Exercise, ExerciseResult)
                .join(
                    ExerciseResult,
                    and_(
                        Exercise.id == ExerciseResult.exercise_id,
                        ExerciseResult.userinfo_id == self.authenticated_user_info.id,
                    ),
                    isouter=True,
                )
                # only load exercises that have no deadline
                # or the deadline is in the future
                .where(
                    or_(
                        Exercise.deadline == None,
                        Exercise.deadline > datetime.now(ZoneInfo(TIME_ZONE)),  # type: ignore
                    )
                )
            )
            exercises_with_result = session.exec(stmt).all()

            self.exercises_with_result = [(x[0], x[1]) for x in exercises_with_result]

            # remove hidden exercises and not started exercises
            self.exercises_with_result = [
                (exercise, result)
                for exercise, result in self.exercises_with_result
                if not exercise.is_hidden and exercise.is_started
            ]

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises_with_result = []

    @rx.var
    def completed_exercises_num(self) -> int:
        """Number of completed exercises."""
        return sum(
            1
            for _, result in self.exercises_with_result
            if result and result.finished_conversation
        )

    @rx.var
    def progress_value(self) -> int:
        """Progress value for the progress bar."""
        total = len(self.exercises_with_result)
        return int((self.completed_exercises_num / total) * 100) if total > 0 else 100

    @rx.var
    def next_deadline_task(self) -> str:
        """Next task with deadline."""
        time_now = datetime.now(ZoneInfo(TIME_ZONE))

        tasks = [
            (ex.title, ex.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE)))
            for ex, res in self.exercises_with_result
            if ex.deadline
            and ex.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE)) > time_now
            and not (res and res.finished_conversation)  # not submitted
        ]

        if not tasks:
            return ""

        title, deadline = min(tasks, key=lambda t: t[1])
        return f"{title} – {deadline.strftime('%d.%m.%Y, %H:%M')}"
