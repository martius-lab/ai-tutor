"""State for the student Beta AI finished view."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserRole


class BetaAIFinishedViewState(SessionState):
    """Student-facing view of a submitted Beta AI conversation."""

    _beta_exercise_id: int
    messages: list[dict[str, str]] = []
    exercise_title: str = ""

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Load the submitted Beta AI conversation for the current student."""
        self.global_load()
        userinfo = self.authenticated_user_info
        if userinfo is None or userinfo.id is None:
            yield rx.redirect(routes.LOGIN)
            return

        try:
            self._beta_exercise_id = self.get_route_param_or_error(
                "beta_exercise_id", dtype=int
            )
        except KeyError, ValueError:
            yield rx.redirect(routes.NOT_FOUND)
            return

        with rx.session() as session:
            result = session.exec(
                select(BetaExercise, BetaExerciseResult.finished_conversation)
                .join(BetaExerciseResult)
                .where(
                    BetaExercise.id == self._beta_exercise_id,
                    BetaExerciseResult.userinfo_id == userinfo.id,
                    BetaExerciseResult.submit_time_stamp != None,  # noqa: E711
                )
            ).one_or_none()
            if result is None:
                yield rx.redirect(routes.NOT_FOUND)
                return
            exercise, finished_conversation = result
            self.exercise_title = exercise.title
            self.messages = list(finished_conversation)

    def on_logout(self):
        """Clear state on logout."""
        self.messages = []
        self.exercise_title = ""

    @rx.var
    def chat_url(self) -> str:
        """Return the Beta AI chat URL."""
        return f"{routes.BETA_AI_CHAT}/{self._beta_exercise_id}"
