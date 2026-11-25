"""The state for the home page."""

from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import and_, func, or_, select

from aitutor.auth.protection import state_require_login
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, LinkUserLecture

ExerciseWithResult = tuple[Exercise, ExerciseResult | None]
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
            Exercise.is_hidden.is_(False),  # type: ignore[attr-defined]
            or_(
                Exercise.deadline == None,
                Exercise.deadline > now,  # type: ignore[operator]
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
        Exercise.deadline,  # type: ignore[arg-type]
    )


class HomeState(SessionState):
    """The state for the home page."""

    num_total_exercises: int = 0
    num_completed_exercises: int = 0
    progress_value: int = 0
    next_deadline_task: str = ""
    lecture_exercise_groups: list[LectureExerciseGroup] = []

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

            exercises_with_result: list[ExerciseWithResult] = [
                (exercise, result) for exercise, result, _ in started_rows
            ]
            self.num_total_exercises = len(exercises_with_result)
            self.num_completed_exercises = sum(
                1
                for _, result in exercises_with_result
                if result and result.finished_conversation
            )
            self.progress_value = (
                int((self.num_completed_exercises / self.num_total_exercises) * 100)
                if self.num_total_exercises > 0
                else 100
            )
            self.next_deadline_task = self._next_deadline_task(exercises_with_result)

            self.lecture_exercise_groups = self._group_exercises_by_lecture(
                started_rows
            )

    @staticmethod
    def _next_deadline_task(exercises_with_result: list[ExerciseWithResult]) -> str:
        """Next task with deadline."""
        time_now = datetime.now(ZoneInfo(TIME_ZONE))

        tasks = [
            (ex.title, ex.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE)))
            for ex, res in exercises_with_result
            if ex.deadline
            and ex.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE)) > time_now
            and not (res and res.finished_conversation)  # not submitted
        ]

        if not tasks:
            return ""

        title, deadline = min(tasks, key=lambda t: t[1])
        return f"{title} – {deadline.strftime('%d.%m.%Y, %H:%M')}"

    @staticmethod
    def _group_exercises_by_lecture(
        rows: Sequence[tuple[Exercise, ExerciseResult | None, Lecture]],
    ) -> list[LectureExerciseGroup]:
        """Group exercise rows by lecture while preserving query order."""
        grouped: dict[int, LectureExerciseGroup] = {}
        for exercise, result, lecture in rows:
            assert lecture.id is not None
            if lecture.id not in grouped:
                grouped[lecture.id] = (lecture, [])
            grouped[lecture.id][1].append((exercise, result))
        return list(grouped.values())
