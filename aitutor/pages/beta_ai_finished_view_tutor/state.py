"""State for the tutor Beta AI finished view."""

from typing import cast

import reflex as rx
from reflex_local_auth import LocalUser
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserInfo, UserRole


class BetaAIFinishedViewTutorState(SessionState):
    """Tutor-facing view of a submitted Beta AI conversation."""

    messages: list[dict[str, str]] = []
    exercise_title: str = ""
    username: str = ""

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.TUTOR)
    def on_load(self):
        """Load the submitted Beta AI conversation and student info."""
        self.global_load()
        try:
            beta_exercise_id = self.get_route_param_or_error(
                "beta_exercise_id", dtype=int
            )
            url_user_id = self.get_route_param_or_error("url_user_id", dtype=int)
        except KeyError, ValueError:
            yield rx.redirect(routes.NOT_FOUND)
            return

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
                    BetaExercise.id == beta_exercise_id,
                    LocalUser.id == url_user_id,
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
        self.exercise_title = ""
        self.username = ""
