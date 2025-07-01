"""The state for the submissions page."""

import reflex as rx
from reflex_local_auth.user import LocalUser
from reflex_local_auth.login import LoginState
from sqlmodel import and_, select
from aitutor import routes
from dataclasses import dataclass

from aitutor.models import ExerciseResult, UserInfo, Exercise, UserRole
from aitutor.auth.state import SessionState


@dataclass
class TableRow:
    """A row in the submissions table."""

    username: str
    user_id: int | None
    role: str
    has_submitted: bool


class SubmissionsState(SessionState):
    """State for the submissions page."""

    exercise_title: str = ""
    table_rows: list[TableRow]

    @rx.var
    def finished_view_teacher_url(self) -> str:
        """
        The exercise_id is used to identify the current exercise.
        It is set by the route parameter in the URL.
        """
        return (
            f"{routes.FINISHED_VIEW_TEACHER}/"
            f"{self.router.page.params.get('exercise_id', 0)}/"
        )

    @rx.event
    def on_load(self):
        """Loads the users and the submissions."""
        # protect data against unauthorized access
        if not self.is_authenticated:
            return LoginState.redir

        with rx.session() as session:
            stmt = (
                select(
                    LocalUser.username,
                    LocalUser.id,
                    UserInfo.role,
                    ExerciseResult.finished_conversation,
                )
                .join(
                    UserInfo,
                    LocalUser.id == UserInfo.user_id,  # type: ignore
                )
                .join(
                    ExerciseResult,
                    and_(
                        LocalUser.id == ExerciseResult.userinfo_id,
                        ExerciseResult.exercise_id == int(self.exercise_id),
                    ),
                    isouter=True,
                )
            )
            self.table_rows = [
                (
                    TableRow(
                        username=x[0],
                        user_id=x[1],
                        role=UserRole(x[2]).name,
                        has_submitted=bool(x[3]),
                    )
                )
                for x in session.exec(stmt).all()
            ]
            title = session.exec(
                select(Exercise.title).where(Exercise.id == int(self.exercise_id))
            ).one_or_none()
            if title:
                self.exercise_title = title

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercise_title = ""
        self.table_rows = []
