"""State for Beta AI tutor submissions."""

from dataclasses import dataclass
from typing import cast

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.models import (
    BetaExercise,
    BetaExerciseResult,
    Lecture,
    LectureRole,
    UserInfo,
)


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
    current_lecture_id: int | None = None

    @rx.event
    @state_require_lecture_role(LectureRole.TUTOR)
    def on_load(self):
        """Load submitted Beta AI exercise results."""
        self.global_load()
        self.current_lecture_id = None
        try:
            lecture_id = self.get_route_param_or_error("lecture_id", dtype=int)
        except Exception:
            return rx.redirect(routes.NOT_FOUND)

        with rx.session() as session:
            if session.get(Lecture, lecture_id) is None:
                return rx.redirect(routes.NOT_FOUND)

        self.current_lecture_id = lecture_id
        self.load_submissions()

    def on_logout(self):
        """Clear state on logout."""
        self.table_rows = []
        self.current_lecture_id = None

    @rx.event
    def load_submissions(self):
        """Load Beta AI results that have a submit timestamp."""
        if self.current_lecture_id is None:
            self.table_rows = []
            return
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
                .where(
                    BetaExercise.lecture_id == self.current_lecture_id,
                    BetaExerciseResult.submit_time_stamp != None,  # noqa: E711
                )
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
