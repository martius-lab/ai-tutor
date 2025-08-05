"""The state for the submissions page."""

import reflex as rx
import sqlalchemy
from reflex_local_auth.user import LocalUser
from sqlmodel import select
from dataclasses import dataclass

from aitutor.models import ExerciseResult, Exercise, UserRole
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least
from aitutor.utilities.parser import parse_query_keys

USER_KEY = "user"
EXERCISE_KEY = "exercise"
TAG_KEY = "tag"


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
    rendered_table_rows: list[TableRow]
    current_search_value: str = ""
    search_values: list[tuple[str, str]] = []
    only_with_submission: bool = False

    @rx.event
    @state_require_role_at_least(UserRole.TEACHER)
    def on_load(self):
        """Loads the users and the submissions."""
        with rx.session() as session:
            stmt = (
                select(LocalUser, Exercise, ExerciseResult)
                .select_from(LocalUser)
                .join(Exercise, sqlalchemy.sql.true())  # cartesian product
                .outerjoin(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == LocalUser.id),  # type: ignore
                )
                .options(sqlalchemy.orm.selectinload(Exercise.tags))
                .order_by(Exercise.title, LocalUser.username)
            )

            for user, exercise, result in session.exec(stmt).all():
                self.table_rows.append(
                    TableRow(
                        username=user.username,
                        user_id=user.id,
                        exercise_id=exercise.id,
                        exercise_title=exercise.title,
                        exercise_tags=[tag.name for tag in exercise.tags],
                        has_submitted=bool(result and result.finished_conversation),
                    )
                )
            # apply filters and fill rendered_table_rows
            self.search_submissions()

    @rx.event
    def search_with_value(self, value: str):
        """Searches the submissions with the given value."""
        self.current_search_value = value
        self.search_submissions()

    @rx.event
    def add_search_value(self, form_data: dict):
        """Adds a search value to the list of search values."""
        parsed = parse_query_keys(
            form_data["search_value"], [TAG_KEY, USER_KEY, EXERCISE_KEY]
        )
        if parsed not in self.search_values:
            self.search_values.append(parsed)
        self.current_search_value = ""
        self.search_submissions()

    @rx.event
    def remove_search_value(self, value: tuple[str, str]):
        """Removes a search value from the list."""
        for v in self.search_values:
            if v[0] == value[0] and v[1] == value[1]:
                self.search_values.remove(v)
                break
        self.search_submissions()

    @rx.event
    def toggle_only_with_submission(self):
        """Toggles the only with submission filter."""
        self.only_with_submission = not self.only_with_submission
        self.search_submissions()

    def search_submissions(self):
        """filters the table based on:
        - current_search_value
        - search_values
        - only_with_submission
        """
        result = self.table_rows
        search_values = self.search_values.copy()

        # append the parsed current search value
        if self.current_search_value:
            parsed = parse_query_keys(
                self.current_search_value, [USER_KEY, EXERCISE_KEY, TAG_KEY]
            )
            if parsed not in self.search_values:
                search_values.append(parsed)

        # filter the result based on search values
        for key, value in search_values:
            value_lower = value.lower()

            if key == USER_KEY:
                result = [row for row in result if value_lower in row.username.lower()]
            elif key == EXERCISE_KEY:
                result = [
                    row for row in result if value_lower in row.exercise_title.lower()
                ]
            elif key == TAG_KEY:
                result = [
                    row
                    for row in result
                    if any(value_lower in tag.lower() for tag in row.exercise_tags)
                ]
            elif key == "rest":
                result = [
                    row
                    for row in result
                    if value_lower in row.username.lower()
                    or value_lower in row.exercise_title.lower()
                    or any(value_lower in tag.lower() for tag in row.exercise_tags)
                ]

        # filter by only with submission
        if self.only_with_submission:
            result = [row for row in result if row.has_submitted]

        self.rendered_table_rows = result

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []
        self.rendered_table_rows = []
        self.current_search_value = ""
        self.search_values = []
        self.only_with_submission = False
