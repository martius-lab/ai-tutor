"""State for the tutor Beta AI finished view."""

from typing import cast

import reflex as rx
from reflex_local_auth import LocalUser
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserInfo, UserRole


class BetaAIFinishedViewTutorState(SessionState):
    """Tutor-facing view of a submitted Beta AI conversation."""

    messages: list[dict[str, str]] = []
    exercise_title: str = "No Beta AI exercise selected"
    username: str = ""

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Load the submitted Beta AI conversation and student info."""
        self.global_load()
        with rx.session() as session:
            result = session.exec(
                select(
                    BetaExercise,
                    LocalUser.username,
                    BetaExerciseResult.finished_conversation,
                )
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
                    BetaExercise.id == int(self.beta_exercise_id),
                    LocalUser.id == int(self.url_user_id),
                    BetaExerciseResult.submit_time_stamp != None,  # noqa: E711
                )
            ).one_or_none()
            if result is None:
                yield rx.redirect(routes.NOT_FOUND)
                return
            exercise, username, finished_conversation = result
            self.exercise_title = exercise.title
            self.username = username
            self.messages = list(finished_conversation)

    def on_logout(self):
        """Clear state on logout."""
        self.messages = []
        self.exercise_title = "No Beta AI exercise selected"
        self.username = ""
