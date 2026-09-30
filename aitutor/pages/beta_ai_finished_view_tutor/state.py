"""State for the tutor Beta AI finished view."""

from typing import cast

import reflex as rx
from reflex_local_auth import LocalUser
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import select

from aitutor import routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserInfo, UserRole
from aitutor.pages.beta_ai_finished_view_tutor.evaluations import (
    EvaluationMessage,
    evaluated_messages,
)
from aitutor.utilities.lecture_permissions import user_may_view_lecture_submissions


class BetaAIFinishedViewTutorState(SessionState):
    """Tutor-facing view of a submitted Beta AI conversation."""

    messages: list[EvaluationMessage] = []
    exercise_title: str = ""
    username: str = ""
    current_lecture_id: int | None = None

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
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
                    BetaExerciseResult.id,
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
                    BetaExerciseResult.submit_time_stamp != None,
                )
            ).one_or_none()
            if result is None:
                yield rx.redirect(routes.NOT_FOUND)
                return
            exercise, username, finished_conversation, result_id = result
            if not self._user_may_view_submission(exercise):
                yield rx.redirect(routes.MY_LECTURES)
                return
            self.exercise_title = exercise.title
            self.current_lecture_id = exercise.lecture_id
            self.username = username
            self.messages = evaluated_messages(
                session,
                session.get(BetaExerciseResult, result_id),
                list(finished_conversation),
            )

    @rx.var
    def submissions_url(self) -> str:
        """Return to the shared submissions page for the current lecture."""
        if self.current_lecture_id is None:
            return routes.MY_LECTURES
        return f"{routes.LECTURE_SUBMISSIONS}/{self.current_lecture_id}"

    def on_logout(self):
        """Clear state on logout."""
        self.messages = []
        self.exercise_title = ""
        self.username = ""
        self.current_lecture_id = None

    def _user_may_view_submission(self, exercise: BetaExercise) -> bool:
        """Return whether the current user may view this Better AI submission."""
        if (
            exercise.lecture_id is None
            or self.authenticated_user is None
            or self.authenticated_user.id is None
        ):
            return False

        with rx.session() as session:
            return user_may_view_lecture_submissions(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=exercise.lecture_id,
            )
