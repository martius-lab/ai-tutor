"""The state for the finished view page."""

import reflex as rx
from typing import Optional
from sqlmodel import select
from reflex_local_auth import LocalUser

import aitutor.routes as routes
from aitutor.models import Exercise, ExerciseResult
from aitutor.auth.state import SessionState
from aitutor.pages.chat.state import ChatMessage, Role


class FinishedViewTeacherState(SessionState):
    """The State for the finished view."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    username: str
    exercise_title: str = "No Exercise Selected"

    @rx.var
    def submissions_url(self) -> str:
        """Returns the URL for the chat page."""
        return (
            f"{routes.SUBMISSIONS}/{str(self.router.page.params.get('exercise_id', 0))}"
        )

    @rx.event
    def on_load(self):
        """Loads the finished exercise and user info."""
        with rx.session() as session:
            stmt = (
                select(
                    Exercise, LocalUser.username, ExerciseResult.finished_conversation
                )
                .where(Exercise.id == int(self.exercise_id))
                .where(LocalUser.id == int(self.url_user_id))
                .where(
                    ExerciseResult.exercise_id == Exercise.id,
                    ExerciseResult.userinfo_id == LocalUser.id,
                )
            )
            result = session.exec(stmt).one_or_none()

            if result is None:
                yield rx.redirect(routes.NOT_FOUND)

            exercise, username, finished_conversation = result  # type: ignore
            self.current_exercise = exercise
            self.exercise_title = exercise.title
            self.username = username
            self.messages = []
            self.set_messages_from_conversation(finished_conversation)

    def set_messages_from_conversation(self, finished_conversation):
        """Loads chat messages from a finished conversation into the state variable."""
        for msg in finished_conversation:
            if msg["role"] != Role.SYSTEM.value:
                self.messages.append(
                    ChatMessage(
                        message=msg["content"],
                        role=Role(msg["role"]),
                        check_passed=msg.get("check_passed", False),
                    )
                )
