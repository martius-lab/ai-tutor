"""State for Beta AI tutor submissions."""

from dataclasses import dataclass
from typing import cast

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserInfo, UserRole


@dataclass
class BetaSubmissionRow:
    """A row in the Beta AI submissions table."""

    username: str
    user_id: int | None
    beta_exercise_id: int | None
    exercise_title: str
    has_submitted: bool


class BetaAISubmissionsState(SessionState):
    """State for the Beta AI submissions page."""

    table_rows: list[BetaSubmissionRow] = []

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Load submitted Beta AI exercise results."""
        self.global_load()
        self.load_submissions()

    def on_logout(self):
        """Clear state on logout."""
        self.table_rows = []

    @rx.event
    def load_submissions(self):
        """Load Beta AI results that have a submit timestamp."""
        with rx.session() as session:
            stmt = (
                select(LocalUser, BetaExercise, BetaExerciseResult)
                .select_from(BetaExerciseResult)
                .join(
                    BetaExercise,
                    cast(
                        ColumnElement[bool],
                        BetaExercise.id == BetaExerciseResult.beta_exercise_id,
                    ),
                )
                .join(
                    UserInfo,
                    cast(
                        ColumnElement[bool],
                        UserInfo.id == BetaExerciseResult.userinfo_id,
                    ),
                )
                .join(
                    LocalUser,
                    cast(ColumnElement[bool], LocalUser.id == UserInfo.user_id),
                )
                .where(BetaExerciseResult.submit_time_stamp != None)  # noqa: E711
                .order_by(BetaExercise.title, LocalUser.username)
            )
            self.table_rows = [
                BetaSubmissionRow(
                    username=user.username,
                    user_id=user.id,
                    beta_exercise_id=exercise.id,
                    exercise_title=exercise.title,
                    has_submitted=result.submit_time_stamp is not None,
                )
                for user, exercise, result in session.exec(stmt).all()
            ]
