"""The state for the finished view page."""

import reflex as rx
from typing import Optional
from sqlmodel import select
from reflex_local_auth import LocalUser

import aitutor.routes as routes
from aitutor.models import Exercise, ExerciseResult, UserInfo, UserRole
from aitutor.auth.state import SessionState
from aitutor.pages.chat.state import ChatMessage, Role
from aitutor.auth.protection import state_require_role_at_least


class FinishedViewTeacherState(SessionState):
    """The State for the finished view."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    username: str
    exercise_title: str = "No Exercise Selected"

    @rx.event
    @state_require_role_at_least(UserRole.TEACHER)
    def on_load(self):
        """Loads the finished exercise and user info."""

        self.global_load()
        with rx.session() as session:
            stmt = (
                select(
                    Exercise, LocalUser.username, ExerciseResult.finished_conversation
                )
                .join(ExerciseResult)
                .join(UserInfo)
                .join(LocalUser)
                .where(
                    Exercise.id == int(self.exercise_id),
                    LocalUser.id == int(self.url_user_id),
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

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.messages = []
        self.current_exercise = None
        self.username = ""
        self.exercise_title = "No Exercise Selected"
