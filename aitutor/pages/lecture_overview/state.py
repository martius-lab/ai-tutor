"""State for the lecture overview page."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import and_, or_, select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, UserRole
from aitutor.utilities.lecture_permissions import user_may_view_lecture


class LectureOverviewState(SessionState):
    """State for one lecture-specific overview page."""

    current_lecture_id: int | None = None
    lecture_name: str = ""
    lecturer_name: str = ""
    lecture_information_text: str = ""
    exercises_with_result: list[tuple[Exercise, Optional[ExerciseResult]]] = []

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the lecture overview state when the page loads."""
        self.global_load()
        self._reset_lecture_state()

        lecture_id_param = self._get_route_lecture_id_param()
        try:
            lecture_id = int(lecture_id_param)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)
            self._apply_lecture_to_state(lecture)

        assert self.authenticated_user_info is not None
        self._load_lecture_exercises()

    def on_logout(self):
        """Clear lecture-specific state when the user logs out."""
        self._reset_lecture_state()

    def _reset_lecture_state(self) -> None:
        """Reset all page-local state values."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.lecturer_name = ""
        self.lecture_information_text = ""
        self.exercises_with_result = []

    def _apply_lecture_to_state(self, lecture: Lecture) -> None:
        """Copy the loaded lecture into state variables for rendering."""
        self.current_lecture_id = lecture.id
        self.lecture_name = lecture.lecture_name
        self.lecturer_name = lecture.lecturer_name
        self.lecture_information_text = lecture.lecture_information_text

    def _load_lecture_exercises(self) -> None:
        """Load visible, started exercises for the selected lecture and current user."""
        if self.current_lecture_id is None:
            self.exercises_with_result = []
            return

        with rx.session() as session:
            stmt = (
                select(Exercise, ExerciseResult)
                .join(
                    ExerciseResult,
                    and_(
                        Exercise.id == ExerciseResult.exercise_id,
                        ExerciseResult.userinfo_id == self.authenticated_user_info.id,  # type: ignore
                    ),
                    isouter=True,
                )
                .where(Exercise.lecture_id == self.current_lecture_id)
                # only load exercises that have no deadline
                # or the deadline is in the future
                .where(
                    or_(
                        Exercise.deadline == None,  # noqa: E711
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

    @rx.var
    def completed_exercises_num(self) -> int:
        """Number of completed lecture exercises."""
        return sum(
            1
            for _, result in self.exercises_with_result
            if result and result.finished_conversation
        )

    @rx.var
    def progress_value(self) -> int:
        """Progress value for the lecture-specific progress bar."""
        total = len(self.exercises_with_result)
        return int((self.completed_exercises_num / total) * 100) if total > 0 else 100

    @rx.var
    def next_deadline_task(self) -> str:
        """Next lecture exercise with a deadline."""
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

    def _get_route_lecture_id_param(self) -> str:
        """Return the lecture id route parameter."""
        return str(self.lecture_id)

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
