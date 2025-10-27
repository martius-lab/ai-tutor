"""The state for the submissions page."""

import reflex as rx
import sqlalchemy
from typing import override
from reflex_local_auth.user import LocalUser
from sqlmodel import select, and_, func
from dataclasses import dataclass
from sqlalchemy.orm import selectinload

from aitutor.models import ExerciseResult, Exercise, UserInfo, UserRole, Tag
from aitutor.auth.state import SessionState
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.auth.protection import state_require_role_at_least
import aitutor.global_vars as gv


@dataclass
class TableRow:
    """A row in the submissions table."""

    username: str
    user_id: int | None
    has_submitted: bool
    exercise_id: int | None
    exercise_title: str
    exercise_tags: list[str]


class SubmissionsState(FilterMixin, SessionState):
    """State for the submissions page."""

    table_rows: list[TableRow]

    # valid search keys. overrides the var from FilterMixin
    search_keys: list[str] = [
        gv.SEARCH_USER_KEY,
        gv.SEARCH_EXERCISE_KEY,
        gv.SEARCH_TAG_KEY,
    ]

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """gets executed when the page loads."""
        self.global_load()
        self.load_submissions()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []
        self.search_values = []  # from FilterMixin

    @override
    @rx.event
    def load_filtered_data(self):
        """implements the abstract method from FilterMixin"""
        self.load_submissions()

    def load_submissions(self):
        """Get submissions from db based on the current search values."""
        with rx.session() as session:
            # statement to load all submissions
            stmt = (
                select(LocalUser, UserInfo, Exercise, ExerciseResult)
                .select_from(LocalUser)
                .join(UserInfo)
                .join(Exercise, sqlalchemy.sql.true())  # cartesian product
                .outerjoin(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == UserInfo.id),  # type: ignore
                )
                .options(selectinload(Exercise.tags))  # type: ignore
                .order_by(func.lower(Exercise.title), LocalUser.username)
            )

            # filter only with submissions
            # (comment out to test if everything is loaded correctly)
            stmt = stmt.where(ExerciseResult.submit_time_stamp != None)  # noqa: E711

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
                TableRow(
                    username=user.username,
                    user_id=user.id,
                    exercise_id=exercise.id,
                    exercise_title=exercise.title,
                    exercise_tags=[tag.name for tag in exercise.tags],
                    has_submitted=bool(result and result.finished_conversation),
                )
                for user, _, exercise, result in session.exec(stmt).all()
            ]
