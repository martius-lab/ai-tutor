"""The state for the home page."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import and_, func, or_, select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import (
    BetaExercise,
    BetaExerciseResult,
    Exercise,
    ExerciseResult,
    Lecture,
    LinkUserLecture,
    UserRole,
)


@dataclass
class HomeExerciseCard:
    """Common home card data for Alpha Tutor and Better AI exercises."""

    title: str
    deadline: datetime | None
    is_beta: bool
    is_submitted: bool
    chat_route: str


LectureExerciseGroup = tuple[Lecture, list[HomeExerciseCard]]


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


def build_home_beta_exercises_statement(
    *,
    userinfo_id: int,
    user_id: int,
    is_global_admin: bool,
    now: datetime,
):
    """Build the query for Better AI exercises visible on the global home page."""
    stmt = (
        select(BetaExercise, BetaExerciseResult, Lecture)
        .join(Lecture, BetaExercise.lecture_id == Lecture.id)  # type: ignore[arg-type]
        .join(
            BetaExerciseResult,
            and_(
                BetaExercise.id == BetaExerciseResult.beta_exercise_id,
                BetaExerciseResult.userinfo_id == userinfo_id,
            ),
            isouter=True,
        )
        .where(
            BetaExercise.is_hidden.is_(False),  # type: ignore[attr-defined]
            or_(
                BetaExercise.deadline == None,
                BetaExercise.deadline > now,  # type: ignore[operator]
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
        BetaExercise.deadline,  # type: ignore[arg-type]
    )


class HomeState(SessionState):
    """The state for the home page."""

    exercise_cards: list[HomeExerciseCard] = []
    lecture_exercise_groups: list[LectureExerciseGroup] = []

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load exercises when the home page is loaded."""
        self.global_load()

        assert self.authenticated_user_info is not None
        assert self.authenticated_user is not None
        assert self.authenticated_user.id is not None
        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            stmt = build_home_exercises_statement(
                userinfo_id=self.authenticated_user_info.id,  # type: ignore[arg-type]
                user_id=self.authenticated_user.id,
                is_global_admin=self.is_global_admin,
                now=now,
            )
            rows = session.exec(stmt).all()

            beta_stmt = build_home_beta_exercises_statement(
                userinfo_id=self.authenticated_user_info.id,  # type: ignore[arg-type]
                user_id=self.authenticated_user.id,
                is_global_admin=self.is_global_admin,
                now=now,
            )
            beta_rows = session.exec(beta_stmt).all()

            started_rows = [
                (
                    HomeExerciseCard(
                        title=exercise.title,
                        deadline=exercise.deadline,
                        is_beta=False,
                        is_submitted=bool(result and result.finished_conversation),
                        chat_route=f"{routes.CHAT}/{exercise.id}",
                    ),
                    lecture,
                )
                for exercise, result, lecture in rows
                if exercise.is_started
            ]
            started_rows.extend(
                (
                    HomeExerciseCard(
                        title=exercise.title,
                        deadline=exercise.deadline,
                        is_beta=True,
                        is_submitted=bool(result and result.finished_conversation),
                        chat_route=f"{routes.BETA_AI_CHAT}/{exercise.id}",
                    ),
                    lecture,
                )
                for exercise, result, lecture in beta_rows
                if exercise.is_started
            )
            started_rows.sort(
                key=lambda row: (
                    row[1].lecture_name.lower(),
                    row[0].deadline or datetime.max,
                )
            )
            self.exercise_cards = [exercise for exercise, _ in started_rows]
            self.lecture_exercise_groups = self._group_exercises_by_lecture(
                started_rows
            )

    @rx.var
    def completed_exercises_num(self) -> int:
        """Number of completed exercises."""
        return sum(1 for exercise in self.exercise_cards if exercise.is_submitted)

    @rx.var
    def progress_value(self) -> int:
        """Progress value for the progress bar."""
        total = len(self.exercise_cards)
        return int((self.completed_exercises_num / total) * 100) if total > 0 else 100

    @rx.var
    def next_deadline_task(self) -> str:
        """Next task with deadline."""
        time_now = datetime.now(ZoneInfo(TIME_ZONE))
        tasks: list[tuple[str, datetime]] = []
        for exercise in self.exercise_cards:
            if exercise.deadline is None or exercise.is_submitted:
                continue

            deadline = exercise.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
            if deadline > time_now:
                tasks.append((exercise.title, deadline))

        if not tasks:
            return ""

        title, deadline = min(tasks, key=lambda t: t[1])
        return f"{title} – {deadline.strftime('%d.%m.%Y, %H:%M')}"

    def _group_exercises_by_lecture(
        self,
        rows: Sequence[tuple[HomeExerciseCard, Lecture]],
    ) -> list[LectureExerciseGroup]:
        """Group exercise rows by lecture while preserving query order."""
        grouped: dict[int, LectureExerciseGroup] = {}
        for exercise, lecture in rows:
            assert lecture.id is not None
            if lecture.id not in grouped:
                grouped[lecture.id] = (lecture, [])
            grouped[lecture.id][1].append(exercise)
        return list(grouped.values())
