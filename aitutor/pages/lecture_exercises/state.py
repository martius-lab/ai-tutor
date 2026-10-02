"""State for the exercises page."""

from dataclasses import dataclass
from datetime import datetime
from typing import override
from zoneinfo import ZoneInfo

import reflex as rx
from sqlalchemy.orm import selectinload
from sqlmodel import Session, and_, func, or_, select

import aitutor.global_vars as gv
from aitutor import routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.global_vars import TIME_ZONE
from aitutor.models import (
    BetaExercise,
    BetaExerciseResult,
    Exercise,
    ExerciseResult,
    Lecture,
    LectureRole,
    Tag,
)
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.utilities.helper_functions import deadline_sort_key
from aitutor.utilities.lecture_permissions import (
    user_may_view_lecture,
    user_may_view_lecture_submissions,
)


@dataclass
class ExerciseCard:
    """Common card data for Alpha Tutor and Beta AI exercises."""

    id: int
    title: str
    description: str
    deadline: datetime | None
    deadline_exceeded: bool
    is_hidden: bool
    is_beta: bool
    is_submitted: bool
    submit_time_stamp: str
    tags: list[str]
    chat_route: str


class LectureExercisesState(FilterMixin, SessionState):
    """State for managing exercises belonging to one lecture."""

    _lecture_id: int
    exercise_cards: list[ExerciseCard] = []
    open_deadline_exercises: list[ExerciseCard] = []
    no_deadline_exercises: list[ExerciseCard] = []
    closed_deadline_exercises: list[ExerciseCard] = []
    time_left_strings: dict[str, str] = {}
    show_submitted_exercises: bool = True
    show_closed_exercises: bool = True

    # valid search keys. overrides the var from FilterMixin
    search_keys: list[str] = [
        gv.SEARCH_EXERCISE_TITLE_KEY,
        gv.SEARCH_EXERCISE_DESCRIPTION_KEY,
        gv.SEARCH_TAG_KEY,
    ]

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def toggle_show_submitted_exercises(self):
        """Toggle the visibility of submitted exercises."""
        self.show_submitted_exercises = not self.show_submitted_exercises
        self.load_exercises()

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def toggle_show_closed_exercises(self):
        """Toggle the visibility of closed exercises."""
        self.show_closed_exercises = not self.show_closed_exercises
        self.load_exercises()

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def on_load(self):
        """
        Fetch exercises from database for the lecture in the route.
        """
        self._global_load()
        assert self._authenticated_user_info is not None
        self._clear_exercises()

        try:
            self._lecture_id = self._get_route_param_or_error("lecture_id", dtype=int)
        except KeyError, ValueError, TypeError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(self._lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, self._lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.load_exercises()

    @rx.var
    def route_lecture_id(self) -> str:
        """Return the lecture id route parameter for lecture-specific navigation."""
        return str(self._lecture_id)

    def _clear_exercises(self):
        """Clear loaded exercise lists."""
        self._lecture_id = -1
        self.exercise_cards = []
        self.open_deadline_exercises = []
        self.no_deadline_exercises = []
        self.closed_deadline_exercises = []
        self.time_left_strings = {}

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

    @override
    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def load_filtered_data(self):
        """implements the abstract method from FilterMixin"""
        self.load_exercises()

    @rx.event
    def update_time_left_strings(self):
        """get the datetime time left for every exercise"""
        time_left_strings = {}
        for exercise in self.exercise_cards:
            if exercise.deadline:
                deadline = exercise.deadline.replace(tzinfo=ZoneInfo(TIME_ZONE))
                time_left = deadline - datetime.now(ZoneInfo(TIME_ZONE))
                if time_left.total_seconds() <= 0:
                    time_left_strings[exercise.chat_route] = ""
                else:
                    days = time_left.days
                    hours, remainder = divmod(time_left.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    time_left_strings[exercise.chat_route] = (
                        f"{days}d {hours}h {minutes}m"
                    )
        self.time_left_strings = time_left_strings

    def load_exercises(self):
        """
        Get exercises from db based on the current search values and the user role.
        """
        user = self.authenticated_user
        if self._lecture_id is None or user is None or user.id is None:
            self._clear_exercises()
            return

        with rx.session() as session:
            cards = self._load_alpha_exercise_cards(
                session
            ) + self._load_beta_exercise_cards(session)

        self.exercise_cards = cards
        self._fill_exercise_groups()
        self.update_time_left_strings()

    def _load_alpha_exercise_cards(self, session: Session) -> list[ExerciseCard]:
        """Load Alpha Tutor exercises as common card data."""
        user = self.authenticated_user
        if self._lecture_id is None or user is None or user.id is None:
            return []
        stmt = (
            select(Exercise, ExerciseResult)
            .options(
                selectinload(Exercise.tags),  # type: ignore
            )
            .join(
                ExerciseResult,
                and_(
                    Exercise.id == ExerciseResult.exercise_id,
                    ExerciseResult.userinfo_id == self._authenticated_user_info.id,  # type: ignore
                ),
                isouter=True,
            )
            .where(Exercise.lecture_id == self._lecture_id)
        )

        # Don't load hidden exercises for students
        can_preview = user_may_view_lecture_submissions(
            session,
            user_id=user.id,
            global_permissions=self.global_permissions,
            lecture_id=self._lecture_id,
        )
        if not can_preview:
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

        # Load Alpha Tutor exercises.
        exercises_with_result = session.exec(
            stmt.order_by(func.lower(Exercise.title))
        ).all()
        return [
            self._alpha_exercise_card(exercise, result)
            for exercise, result in exercises_with_result
            if can_preview or exercise.is_started
        ]

    def _alpha_exercise_card(
        self, exercise: Exercise, result: ExerciseResult | None
    ) -> ExerciseCard:
        """Convert an Alpha Tutor exercise to common card data."""
        assert exercise.id is not None
        return ExerciseCard(
            id=exercise.id,
            title=exercise.title,
            description=exercise.description,
            deadline=exercise.deadline,
            deadline_exceeded=exercise.deadline_exceeded,
            is_hidden=exercise.is_hidden or not exercise.is_started,
            is_beta=False,
            is_submitted=bool(result and result.finished_conversation),
            submit_time_stamp=(
                result.submit_time_stamp.isoformat()
                if result is not None and result.submit_time_stamp is not None
                else ""
            ),
            tags=[tag.name for tag in exercise.tags],
            chat_route=f"{routes.CHAT}/{exercise.id}",
        )

    def _load_beta_exercise_cards(self, session: Session) -> list[ExerciseCard]:
        """Load Beta AI exercises as common card data."""
        user = self.authenticated_user
        if self._lecture_id is None or user is None or user.id is None:
            return []
        stmt = (
            select(BetaExercise, BetaExerciseResult)
            .options(selectinload(BetaExercise.tags))  # type: ignore
            .join(
                BetaExerciseResult,
                and_(
                    BetaExercise.id == BetaExerciseResult.beta_exercise_id,
                    BetaExerciseResult.userinfo_id == self._authenticated_user_info.id,  # type: ignore
                ),
                isouter=True,
            )
            .where(BetaExercise.lecture_id == self._lecture_id)
        )

        can_preview = user_may_view_lecture_submissions(
            session,
            user_id=user.id,
            global_permissions=self.global_permissions,
            lecture_id=self._lecture_id,
        )
        if not can_preview:
            stmt = stmt.where(BetaExercise.is_hidden == False)  # noqa: E712

        for key, value in self.search_values:
            match key:
                case gv.SEARCH_EXERCISE_TITLE_KEY:
                    stmt = stmt.where(BetaExercise.title.ilike(f"%{value}%"))  # type: ignore
                case gv.SEARCH_EXERCISE_DESCRIPTION_KEY:
                    stmt = stmt.where(BetaExercise.description.ilike(f"%{value}%"))  # type: ignore
                case gv.SEARCH_TAG_KEY:
                    stmt = stmt.where(
                        BetaExercise.tags.any(Tag.name.ilike(f"%{value}%"))  # type: ignore
                    )
                case _:
                    stmt = stmt.where(
                        or_(
                            BetaExercise.title.ilike(f"%{value}%"),  # type: ignore
                            BetaExercise.description.ilike(f"%{value}%"),  # type: ignore
                            BetaExercise.tags.any(Tag.name.ilike(f"%{value}%")),  # type: ignore
                        )
                    )

        cards = []
        for exercise, result in session.exec(stmt).all():
            assert exercise.id is not None, "Persisted Beta AI exercise has no ID."
            if not can_preview and not exercise.is_started:
                continue
            cards.append(
                ExerciseCard(
                    id=exercise.id,
                    title=exercise.title,
                    description=exercise.description,
                    deadline=exercise.deadline,
                    deadline_exceeded=exercise.deadline_exceeded,
                    is_hidden=exercise.is_hidden or not exercise.is_started,
                    is_beta=True,
                    is_submitted=bool(result and result.finished_conversation),
                    submit_time_stamp=(
                        result.submit_time_stamp.isoformat()
                        if result is not None and result.submit_time_stamp is not None
                        else ""
                    ),
                    tags=[tag.name for tag in exercise.tags],
                    chat_route=f"{routes.BETA_AI_CHAT}/{exercise.lecture_id}/{exercise.id}",
                )
            )
        return cards

    def _fill_exercise_groups(self):
        """Apply the existing filters and sorting to all exercise cards."""
        self.open_deadline_exercises = []
        self.no_deadline_exercises = []
        self.closed_deadline_exercises = []

        for exercise in self.exercise_cards:
            if not self.show_submitted_exercises and exercise.is_submitted:
                continue
            if not self.show_closed_exercises and exercise.deadline_exceeded:
                continue

            if exercise.deadline_exceeded:
                self.closed_deadline_exercises.append(exercise)
            elif exercise.deadline is None:
                self.no_deadline_exercises.append(exercise)
            else:
                self.open_deadline_exercises.append(exercise)

        self.open_deadline_exercises.sort(
            key=lambda exercise: deadline_sort_key(exercise.deadline)
        )
        self.closed_deadline_exercises.sort(
            key=lambda exercise: deadline_sort_key(exercise.deadline),
            reverse=True,
        )
        self.no_deadline_exercises.sort(
            key=lambda exercise: (exercise.is_submitted, exercise.title.lower())
        )
