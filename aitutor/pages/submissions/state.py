"""The state for the submissions page."""

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlmodel import literal_column, select
from dataclasses import dataclass

from aitutor.models import ExerciseResult, Exercise, UserRole
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least


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
    search_values: list[str] = []
    only_with_submission: bool = False

    @rx.event
    @state_require_role_at_least(UserRole.TEACHER)
    def on_load(self):
        """Loads the users and the submissions."""
        with rx.session() as session:
            stmt = (
                select(
                    LocalUser.username,
                    LocalUser.id,
                    Exercise.id,
                    Exercise.title,
                    Exercise.tags,
                    ExerciseResult.finished_conversation,
                )  # type: ignore
                .select_from(LocalUser)
                # cartesian product
                .join(Exercise, literal_column("1") == literal_column("1"))
                .outerjoin(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == LocalUser.id),
                )
                .order_by(Exercise.title, LocalUser.username)
            )
            self.table_rows = [
                (
                    TableRow(
                        username=x[0],
                        user_id=x[1],
                        exercise_id=x[2],
                        exercise_title=x[3],
                        exercise_tags=x[4],
                        has_submitted=bool(x[5]),
                    )
                )
                for x in session.exec(stmt).all()
            ]
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
        if form_data["search_value"] not in self.search_values:
            self.search_values.append(form_data["search_value"])
        self.current_search_value = ""
        self.search_submissions()

    @rx.event
    def remove_search_value(self, value: str):
        """Removes a search value from the list."""
        if value in self.search_values:
            self.search_values.remove(value)
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
        if self.current_search_value != "":
            search_term = self.current_search_value.lower()
            result = [
                row
                for row in result
                if search_term in row.username.lower()
                or search_term in row.exercise_title.lower()
                or any(search_term in tag.lower() for tag in row.exercise_tags)
            ]
        if self.search_values:
            for search_value in self.search_values:
                result = [
                    row
                    for row in result
                    if search_value.lower() in row.username.lower()
                    or search_value.lower() in row.exercise_title.lower()
                    or any(
                        search_value.lower() in tag.lower() for tag in row.exercise_tags
                    )
                ]
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
