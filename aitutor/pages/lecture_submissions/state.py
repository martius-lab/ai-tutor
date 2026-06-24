"""The state for the lecture-specific submissions page."""

from dataclasses import dataclass
from typing import override

import reflex as rx
import sqlalchemy
from reflex_local_auth.user import LocalUser
from sqlalchemy.orm import selectinload
from sqlmodel import and_, func, or_, select

import aitutor.global_vars as gv
import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.config import get_config
from aitutor.models import (
    Exercise,
    ExerciseResult,
    Lecture,
    Tag,
    UserInfo,
    UserRole,
)
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.utilities.lecture_permissions import user_may_view_lecture_submissions


@dataclass
class LectureSubmissionTableRow:
    """A row in the lecture-specific submissions table."""

    username: str
    user_id: int | None
    has_submitted: bool
    token_limit_reached: bool
    exercise_id: int | None
    exercise_title: str
    exercise_tags: list[str]


class LectureSubmissionsState(FilterMixin, SessionState):
    """State for the lecture-specific submissions page."""

    current_lecture_id: int | None = None
    table_rows: list[LectureSubmissionTableRow]

    # valid search keys. overrides the var from FilterMixin
    search_keys: list[str] = [
        gv.SEARCH_USER_KEY,
        gv.SEARCH_EXERCISE_KEY,
        gv.SEARCH_TAG_KEY,
    ]

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Gets executed when the page loads."""
        self.global_load()
        self.current_lecture_id = None
        self.table_rows = []

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_submissions(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.load_submissions()

    def _user_may_view_submissions(self, lecture_id: int) -> bool:
        """Return whether the current user may view submissions in the lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        with rx.session() as session:
            return user_may_view_lecture_submissions(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=lecture_id,
            )

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.current_lecture_id = None
        self.table_rows = []
        self.search_values = []  # from FilterMixin

    @override
    @rx.event
    def load_filtered_data(self):
        """Implements the abstract method from FilterMixin."""
        self.load_submissions()

    def load_submissions(self):
        """Get submissions from db based on the current lecture and search values."""
        if self.current_lecture_id is None:
            self.table_rows = []
            return

        token_limit = get_config().exercise_token_limit
        with rx.session() as session:
            # statement to load all submissions for this lecture
            stmt = (
                select(LocalUser, UserInfo, Exercise, ExerciseResult)
                .select_from(LocalUser)
                .join(UserInfo)
                .join(Exercise, sqlalchemy.sql.true())  # cartesian product
                .join(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == UserInfo.id),  # type: ignore
                )
                .options(selectinload(Exercise.tags))  # type: ignore
                .where(Exercise.lecture_id == self.current_lecture_id)
                .order_by(func.lower(Exercise.title), LocalUser.username)
            )

            # filter only rows that are either submitted or hit token limit
            stmt = stmt.where(
                or_(
                    ExerciseResult.submit_time_stamp != None,
                    ExerciseResult.tokens_used >= token_limit,
                )
            )

            # filter with search values
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    match key:
                        case gv.SEARCH_USER_KEY:
                            search_conditions.append(
                                LocalUser.username.ilike(f"%{value}%")  # type: ignore
                            )
                        case gv.SEARCH_EXERCISE_KEY:
                            search_conditions.append(
                                Exercise.title.ilike(f"%{value}%")  # type: ignore
                            )
                        case gv.SEARCH_TAG_KEY:
                            search_conditions.append(
                                Exercise.tags.any(Tag.name.ilike(f"%{value}%"))  # type: ignore
                            )
                        case _:
                            search_conditions.append(
                                sqlalchemy.or_(
                                    LocalUser.username.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.title.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.tags.any(Tag.name.ilike(f"%{value}%")),  # type: ignore
                                )
                            )
                stmt = stmt.where(and_(*search_conditions))

            # get submissions from db
            self.table_rows = [
                LectureSubmissionTableRow(
                    username=user.username,
                    user_id=user.id,
                    has_submitted=result.submit_time_stamp is not None,
                    exercise_id=exercise.id,
                    exercise_title=exercise.title,
                    exercise_tags=[tag.name for tag in exercise.tags],
                    token_limit_reached=result.tokens_used >= token_limit,
                )
                for user, _, exercise, result in session.exec(stmt).all()
            ]
