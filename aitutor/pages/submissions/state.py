"""The state for the submissions page."""

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlmodel import literal_column, select
from dataclasses import dataclass

from aitutor.models import ExerciseResult, UserInfo, Exercise, UserRole
from aitutor.auth.state import SessionState
from aitutor.auth.protection import state_require_role_at_least


@dataclass
class TableRow:
    """A row in the submissions table."""

    username: str
    user_id: int | None
    role: str
    has_submitted: bool
    exercise_id: int | None
    exercise_title: str


class SubmissionsState(SessionState):
    """State for the submissions page."""

    table_rows: list[TableRow]

    @rx.event
    @state_require_role_at_least(UserRole.TEACHER)
    def on_load(self):
        """Loads the users and the submissions."""

        with rx.session() as session:
            stmt = (
                select(
                    LocalUser.username,
                    LocalUser.id,
                    UserInfo.role,
                    Exercise.id,
                    Exercise.title,
                    ExerciseResult.finished_conversation,
                )  # type: ignore
                .select_from(LocalUser)
                .join(UserInfo, LocalUser.id == UserInfo.user_id)
                # cartesian product
                .join(Exercise, literal_column("1") == literal_column("1"))
                .outerjoin(
                    ExerciseResult,
                    (ExerciseResult.exercise_id == Exercise.id)
                    & (ExerciseResult.userinfo_id == UserInfo.id),
                )
                .order_by(Exercise.title, LocalUser.username)
            )
            self.table_rows = [
                (
                    TableRow(
                        username=x[0],
                        user_id=x[1],
                        role=UserRole(x[2]).name,
                        exercise_id=x[3],
                        exercise_title=x[4],
                        has_submitted=bool(x[5]),
                    )
                )
                for x in session.exec(stmt).all()
            ]

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.table_rows = []
