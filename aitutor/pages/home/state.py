"""The state for the home page."""

from collections.abc import Sequence
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import and_, func, or_, select

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, LinkUserLecture, UserRole

ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]
LectureExerciseGroup = tuple[Lecture, list[ExerciseWithResult]]


def build_home_exercises_statement(
    *,
    userinfo_id: int,
    user_id: int,
    is_global_admin: bool,
    now: datetime,
):
    """Build the query for exercises visible on the global home page."""
    stmt = (
        select(Exercise, ExerciseResult, Lecture)
        .join(Lecture, Exercise.lecture_id == Lecture.id)  # type: ignore[arg-type]
        .join(
            ExerciseResult,
            and_(
                Exercise.id == ExerciseResult.exercise_id,
                ExerciseResult.userinfo_id == userinfo_id,
            ),
            isouter=True,
        )
        .where(
            or_(
                Exercise.deadline == None,
                Exercise.deadline > now,  # type: ignore[operator]
            )
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
        Exercise.deadline,  # type: ignore[arg-type]
    )


class HomeState(SessionState):
    """The state for the home page."""

    exercises_with_result: list[ExerciseWithResult] = []
    lecture_exercise_groups: list[LectureExerciseGroup] = []

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load exercises when the home page is loaded."""
        self.global_load()

        assert self.authenticated_user_info is not None
        assert self.authenticated_user is not None
        assert self.authenticated_user.id is not None
        with rx.session() as session:
            stmt = build_home_exercises_statement(
                userinfo_id=self.authenticated_user_info.id,  # type: ignore[arg-type]
                user_id=self.authenticated_user.id,
                is_global_admin=self.is_global_admin,
                now=datetime.now(ZoneInfo(TIME_ZONE)),
            )
            rows = session.exec(stmt).all()

            visible_rows = [
                (exercise, result, lecture)
                for exercise, result, lecture in rows
                if not exercise.is_hidden and exercise.is_started
            ]
            self.exercises_with_result = [
                (exercise, result) for exercise, result, _ in visible_rows
            ]
            self.lecture_exercise_groups = self._group_exercises_by_lecture(
                visible_rows
            )

    def _group_exercises_by_lecture(
        self,
        rows: Sequence[tuple[Exercise, Optional[ExerciseResult], Lecture]],
    ) -> list[LectureExerciseGroup]:
        """Group exercise rows by lecture while preserving query order."""
        grouped: dict[int, LectureExerciseGroup] = {}
        for exercise, result, lecture in rows:
            assert lecture.id is not None
            if lecture.id not in grouped:
                grouped[lecture.id] = (lecture, [])
            grouped[lecture.id][1].append((exercise, result))
        return list(grouped.values())

    @rx.var
    def deadline_strings(self) -> dict[int, str]:
        """Return formatted deadlines keyed by exercise id."""
        return {
            exercise.id: exercise.deadline.strftime("%d.%m.%Y, %H:%M")
            if exercise.deadline is not None
            else ""
            for exercise, _ in self.exercises_with_result
            if exercise.id is not None
        }

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
