"""The state for the home page."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlalchemy import Nullable
from sqlmodel import and_, col, func, or_, select

from aitutor.auth.protection import state_require_login
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, LinkUserLecture
from aitutor.utilities.exercises import (
    ExerciseWithDeadline,
    is_submitted,
    next_due_exercise,
)
from aitutor.utilities.helper_functions import to_tz_aware


@dataclass
class ExerciseData:
    """Bundles the data needed about an exercise for the home page."""

    id: int
    title: str
    deadline: datetime | None
    is_submitted: bool


@dataclass
class LectureExercisesData:
    """Bundles the data needed about a lecture and its exercises for the home page."""

    lecture_id: int
    lecture_name: str
    exercises: list[ExerciseData]


def build_home_exercises_statement(
    *,
    userinfo_id: int,
    user_id: int,
    is_global_admin: bool,
    now: datetime,
):
    """Build the query for exercises visible on the global home page."""
    stmt = (
        # `Nullable` is just a type hint (can be null due to outer join)
        select(Exercise, Nullable(ExerciseResult), Lecture)
        .join(Lecture, col(Exercise.lecture_id) == Lecture.id)
        .join(
            ExerciseResult,
            and_(
                Exercise.id == ExerciseResult.exercise_id,
                ExerciseResult.userinfo_id == userinfo_id,
            ),
            isouter=True,
        )
        .where(
            col(Exercise.is_hidden).is_(False),
            or_(
                Exercise.deadline == None,
                col(Exercise.deadline) > now,
            ),
        )
    )

    if not is_global_admin:
        stmt = stmt.join(
            LinkUserLecture,
            and_(
                LinkUserLecture.lecture_id == Lecture.id,
                LinkUserLecture.user_id == user_id,
            ),
        )

    return stmt.order_by(
        func.lower(Lecture.lecture_name),
        col(Exercise.deadline),
    )


def _group_exercises_by_lecture(
    rows: Sequence[tuple[Exercise, ExerciseResult | None, Lecture]],
) -> list[LectureExercisesData]:
    """Group exercise rows by lecture while preserving query order."""
    grouped: dict[int, LectureExercisesData] = {}
    for exercise, result, lecture in rows:
        assert lecture.id is not None
        assert exercise.id is not None

        if lecture.id not in grouped:
            grouped[lecture.id] = LectureExercisesData(
                lecture_id=lecture.id,
                lecture_name=lecture.lecture_name,
                exercises=[],
            )
        grouped[lecture.id].exercises.append(
            ExerciseData(
                id=exercise.id,
                title=exercise.title,
                deadline=(
                    to_tz_aware(exercise.deadline) if exercise.deadline else None
                ),
                is_submitted=is_submitted(result),
            )
        )
    return list(grouped.values())


class HomeState(SessionState):
    """The state for the home page."""

    num_total_exercises: int = 0
    num_completed_exercises: int = 0
    next_due_exercise: ExerciseWithDeadline | None = None
    lecture_exercise_groups: list[LectureExercisesData] = []

    @rx.event
    @state_require_login()
    def on_load(self):
        """Load exercises when the home page is loaded."""
        self._global_load()

        assert self._authenticated_user_info is not None
        assert self.authenticated_user is not None
        assert self.authenticated_user.id is not None
        with rx.session() as session:
            stmt = build_home_exercises_statement(
                userinfo_id=self._authenticated_user_info.id,  # type: ignore[arg-type]
                user_id=self.authenticated_user.id,
                is_global_admin=self.is_global_admin,
                now=datetime.now(ZoneInfo(TIME_ZONE)),
            )
            rows = session.exec(stmt).all()

            started_rows = [
                (exercise, result, lecture)
                for exercise, result, lecture in rows
                if exercise.is_started
            ]

            exercises_with_result = [
                (exercise, result) for exercise, result, _ in started_rows
            ]
            self.num_total_exercises = len(exercises_with_result)
            self.num_completed_exercises = sum(
                1 for _, result in exercises_with_result if is_submitted(result)
            )
            self.next_due_exercise = next_due_exercise(exercises_with_result)

            self.lecture_exercise_groups = _group_exercises_by_lecture(started_rows)
