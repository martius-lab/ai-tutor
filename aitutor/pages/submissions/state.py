"""The state for the submissions page."""

import reflex as rx
import sqlalchemy
import contextlib
from reflex_local_auth.user import LocalUser
from sqlmodel import select, and_
from dataclasses import dataclass
from sqlalchemy.orm import selectinload

from aitutor.models import ExerciseResult, Exercise, UserRole, Tag
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least
from aitutor.utilities.parser import parse_query_keys
from aitutor.global_vars import SEARCH_USER_KEY, SEARCH_EXERCISE_KEY, SEARCH_TAG_KEY


@dataclass
class TableRow:
    """A row in the submissions table."""

    username: str
    user_id: int | None
    has_submitted: bool
    exercise_id: int | None
    exercise_title: str
    exercise_tags: list[str]


class SubmissionsState(SessionState):
    """State for the submissions page."""

    table_rows: list[TableRow]
    search_values: list[tuple[str, str]] = []
    only_with_submission: bool = False

    @rx.event
    @state_require_role_at_least(UserRole.TEACHER)
    def on_load(self):
        """gets executed when the page loads."""
        self.load_submissions()

    @rx.event
    def load_submissions(self):
        """Get submissions from db based on the current search values."""
        with rx.session() as session:
            # statement to load all submissions
            stmt = (
                select(LocalUser, Exercise, ExerciseResult)
                .select_from(LocalUser)
                .join(Exercise, sqlalchemy.sql.true())  # cartesian product
                .outerjoin(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == LocalUser.id),  # type: ignore
                )
                .options(selectinload(Exercise.tags))  # type: ignore
                .order_by(Exercise.title, LocalUser.username)
            )

            # filter with search values
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    if key == SEARCH_USER_KEY:
                        search_conditions.append(
                            LocalUser.username.ilike(f"%{value}%")  # type: ignore
                        )
                    elif key == SEARCH_EXERCISE_KEY:
                        search_conditions.append(
                            Exercise.title.ilike(f"%{value}%")  # type: ignore
                        )
                    elif key == SEARCH_TAG_KEY:
                        search_conditions.append(
                            Exercise.tags.any(Tag.name.ilike(f"%{value}%"))  # type: ignore
                        )
                    else:
                        search_conditions.append(
                            sqlalchemy.or_(
                                LocalUser.username.ilike(f"%{value}%"),  # type: ignore
                                Exercise.title.ilike(f"%{value}%"),  # type: ignore
                                Exercise.tags.any(Tag.name.ilike(f"%{value}%")),  # type: ignore
                            )
                        )
                stmt = stmt.where(and_(*search_conditions))

            # filter with only with submission
            if self.only_with_submission:
                stmt = stmt.where(ExerciseResult.finished_conversation != [])

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
                for user, exercise, result in session.exec(stmt).all()
            ]

    @rx.event
    def add_search_value(self, form_data: dict):
        """Adds a search value to the list of search values."""
        parsed = parse_query_keys(
            form_data["search_value"],
            [SEARCH_TAG_KEY, SEARCH_USER_KEY, SEARCH_EXERCISE_KEY],
        )
        if parsed not in self.search_values:
            self.search_values.append(parsed)
        self.load_submissions()

    @rx.event
    def remove_search_value(self, value: tuple[str, str]):
        """Removes a search value from the list."""
        with contextlib.suppress(ValueError):
            self.search_values.remove(tuple[str, str](value))
        self.load_submissions()

    @rx.event
    def toggle_only_with_submission(self):
        """Toggles the only with submission filter."""
        self.only_with_submission = not self.only_with_submission
        self.load_submissions()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []
        self.search_values = []
        self.only_with_submission = False
