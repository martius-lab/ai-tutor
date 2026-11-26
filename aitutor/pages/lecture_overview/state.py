"""State for the lecture overview page."""

from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlalchemy import Nullable
from sqlmodel import and_, col, or_, select

from aitutor import routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, LectureRole
from aitutor.utilities.exercises import (
    ExerciseWithMaybeResult,
    is_submitted,
    next_deadline_task,
)
from aitutor.utilities.lecture_permissions import user_may_view_lecture


class LectureOverviewState(SessionState):
    """State for one lecture-specific overview page."""

    current_lecture_id: int | None = None
    lecture_name: str = ""
    lecturer_name: str = ""
    lecture_information_text: str = ""

    num_total_exercises: int = 0
    num_completed_exercises: int = 0
    progress_value: int = 0
    next_deadline_task: tuple[str, datetime] | None = None

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def on_load(self):
        """Initialize the lecture overview state when the page loads."""
        self._global_load()
        self._reset_lecture_state()

        try:
            lecture_id = self._get_route_param_or_error("lecture_id", dtype=int)
        except Exception:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)
            self._apply_lecture_to_state(lecture)

        assert self._authenticated_user_info is not None
        exercises_with_result = self._load_lecture_exercises()

        self.num_total_exercises = len(exercises_with_result)
        self.num_completed_exercises = sum(
            1 for _, result in exercises_with_result if is_submitted(result)
        )
        self.progress_value = (
            int((self.num_completed_exercises / self.num_total_exercises) * 100)
            if self.num_total_exercises > 0
            else 100
        )
        self.next_deadline_task = next_deadline_task(exercises_with_result)

    def _reset_lecture_state(self) -> None:
        """Reset all page-local state values."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.lecturer_name = ""
        self.lecture_information_text = ""
        self.num_total_exercises = 0
        self.num_completed_exercises = 0
        self.progress_value = 0
        self.next_deadline_task = None

    def _apply_lecture_to_state(self, lecture: Lecture) -> None:
        """Copy the loaded lecture into state variables for rendering."""
        self.current_lecture_id = lecture.id
        self.lecture_name = lecture.lecture_name
        self.lecturer_name = lecture.lecturer_name
        self.lecture_information_text = lecture.lecture_information_text

    def _load_lecture_exercises(self) -> list[ExerciseWithMaybeResult]:
        """Load visible, started exercises for the selected lecture and current user."""
        if self.current_lecture_id is None:
            return []

        with rx.session() as session:
            stmt = (
                # `Nullable` is just a type hint (can be null due to outer join)
                select(Exercise, Nullable(ExerciseResult))
                .join(
                    ExerciseResult,
                    and_(
                        Exercise.id == ExerciseResult.exercise_id,
                        ExerciseResult.userinfo_id == self._authenticated_user_info.id,  # type: ignore
                    ),
                    isouter=True,
                )
                .where(
                    Exercise.lecture_id == self.current_lecture_id,
                    col(Exercise.is_hidden).is_(False),
                    # only load exercises that have no deadline or the deadline is in
                    # the future
                    or_(
                        Exercise.deadline == None,
                        col(Exercise.deadline) > datetime.now(ZoneInfo(TIME_ZONE)),
                    ),
                )
            )

            exercises_with_result = session.exec(stmt).all()
            return [
                (exercise, result)
                for exercise, result in exercises_with_result
                if exercise.is_started
            ]

    def _user_may_view_lecture(self, lecture_id: int) -> bool:
        """Check whether the current user may open this lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        with rx.session() as session:
            return user_may_view_lecture(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )
