"""State for the student Beta AI finished view."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import BetaExercise, BetaExerciseResult, UserRole


class BetaAIFinishedViewState(SessionState):
    """Student-facing view of a submitted Beta AI conversation."""

    messages: list[dict[str, str]] = []
    exercise_title: str = "No Beta AI exercise selected"

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """Load the submitted Beta AI conversation for the current student."""
        self.global_load()
        userinfo = self.authenticated_user_info
        if userinfo is None or userinfo.id is None:
            yield rx.redirect(routes.LOGIN)
            return

        with rx.session() as session:
            result = session.exec(
                select(BetaExercise, BetaExerciseResult.finished_conversation)
                .join(BetaExerciseResult)
                .where(
                    BetaExercise.id == int(self.beta_exercise_id),
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
        self.exercise_title = "No Beta AI exercise selected"

    @rx.var
    def chat_url(self) -> str:
        """Return the Beta AI chat URL."""
        return f"{routes.BETA_AI_CHAT}/{self.beta_exercise_id}"
