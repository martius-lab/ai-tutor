"""State for the exercises page."""

from datetime import datetime
from typing import Optional, override
from zoneinfo import ZoneInfo

import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, or_, select

import aitutor.global_vars as gv
import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_FORMAT, TIME_ZONE
from aitutor.models import Exercise, ExerciseResult, Lecture, Tag, UserRole
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.utilities.lecture_permissions import user_may_view_lecture

ExerciseWithResult = tuple[Exercise, Optional[ExerciseResult]]


class LectureExercisesState(FilterMixin, SessionState):
    """State for managing exercises belonging to one lecture."""

    exercises_with_result: list[ExerciseWithResult] = []
    open_deadline_exercises: list[ExerciseWithResult] = []
    no_deadline_exercises: list[ExerciseWithResult] = []
    closed_deadline_exercises: list[ExerciseWithResult] = []
    time_left_strings: dict[int, str] = {}  # (exercise_id, time_left_string)
    show_submitted_exercises: bool = True
    show_closed_exercises: bool = True

    # valid search keys. overrides the var from FilterMixin
    search_keys: list[str] = [
        gv.SEARCH_EXERCISE_TITLE_KEY,
        gv.SEARCH_EXERCISE_DESCRIPTION_KEY,
        gv.SEARCH_TAG_KEY,
    ]

    @rx.event
    def toggle_show_submitted_exercises(self):
        """Toggle the visibility of submitted exercises."""
        self.show_submitted_exercises = not self.show_submitted_exercises
        self.load_exercises()

    @rx.event
    def toggle_show_closed_exercises(self):
        """Toggle the visibility of closed exercises."""
        self.show_closed_exercises = not self.show_closed_exercises
        self.load_exercises()

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """
        Fetch exercises from database for the lecture in the route.
        """
        self.global_load()
        assert self.authenticated_user_info is not None
        self._clear_exercises()

        lecture_id = self._parse_route_lecture_id()
        if lecture_id is None:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.load_exercises()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self._clear_exercises()

    @rx.var
    def route_lecture_id(self) -> str:
        """Return the lecture id route parameter for lecture-specific navigation."""
        return str(self.lecture_id)

    def _clear_exercises(self):
        """Clear loaded exercise lists."""
        self.exercises_with_result = []
        self.open_deadline_exercises = []
        self.no_deadline_exercises = []
        self.closed_deadline_exercises = []
        self.time_left_strings = {}

    def _parse_route_lecture_id(self) -> int | None:
        """Return the numeric lecture id from the route, or None if invalid."""
        try:
            return int(self.lecture_id)
        except ValueError:
            return None

    def _user_may_view_lecture(self, lecture_id: int) -> bool:
        """Check whether the current user may view this lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        with rx.session() as session:
            return user_may_view_lecture(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )

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

    @override
    @rx.event
    def load_filtered_data(self):
        """implements the abstract method from FilterMixin"""
        self.load_exercises()

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

    def load_exercises(self):
        """
        Get exercises from db based on the current search values and the user role.
        """
        lecture_id = self._parse_route_lecture_id()
        if lecture_id is None:
            self._clear_exercises()
            return

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
                        ExerciseResult.userinfo_id == self.authenticated_user_info.id,  # type: ignore
                    ),
                    isouter=True,
                )
                .where(Exercise.lecture_id == lecture_id)
            )

            # Don't load hidden exercises for students
            assert self.user_role is not None, "User role not set.  This is a bug."
            if self.user_role < UserRole.TUTOR:
                stmt = stmt.where(Exercise.is_hidden == False)  # noqa: E712

            # filtering logic
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    match key:
                        case gv.SEARCH_EXERCISE_TITLE_KEY:
                            search_conditions.append(
                                Exercise.title.ilike(f"%{value}%")  # type: ignore
                            )
                        case gv.SEARCH_EXERCISE_DESCRIPTION_KEY:
                            search_conditions.append(
                                Exercise.description.ilike(f"%{value}%")  # type: ignore
                            )
                        case gv.SEARCH_TAG_KEY:
                            search_conditions.append(
                                Exercise.tags.any(Tag.name.ilike(f"%{value}%"))  # type: ignore
                            )
                        case _:
                            # Default search across title, description and tags
                            search_conditions.append(
                                or_(
                                    Exercise.title.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.description.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.tags.any(Tag.name.ilike(f"%{value}%")),  # type: ignore
                                )
                            )
                # Apply all conditions with AND
                stmt = stmt.where(and_(*search_conditions))

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
                result = ex_wth_res[1]

                # filter submitted exercises
                is_submitted = (
                    result is not None and result.submit_time_stamp is not None
                )
                if not self.show_submitted_exercises and is_submitted:
                    continue

                # filter closed exercises
                if not self.show_closed_exercises and exercise.deadline_exceeded:
                    continue

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
