"""The state for the finished view page."""

import reflex as rx
from typing import Optional

import aitutor.routes as routes
from aitutor.models import Exercise, ExerciseResult, UserRole
from aitutor.auth.state import SessionState
from aitutor.pages.chat.state import ChatMessage, Role
from sqlmodel import select
from aitutor.auth.protection import state_require_role_at_least


class FinishedViewState(SessionState):
    """The State for the finished view."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    exercise_title: str = "No Exercise Selected"

    @rx.var
    def chat_url(self) -> str:
        """Returns the URL for the chat page."""
        return f"{routes.CHAT}/{self.exercise_id}"

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """Loads the finished exercise and conversation."""

        if self.user_id:
            with rx.session() as session:
                stmt = (
                    select(
                        Exercise,
                        ExerciseResult.finished_conversation,
                    )
                    .join(ExerciseResult)
                    .where(
                        Exercise.id == int(self.exercise_id),
                        ExerciseResult.userinfo_id == self.user_id,
                    )
                )
                result = session.exec(stmt).one_or_none()

                if result is None:
                    yield rx.redirect(routes.NOT_FOUND)

                exercise, finished_conversation = result  # type: ignore
                self.current_exercise = exercise
                self.exercise_title = exercise.title
                self.messages = []
                self.set_messages_from_conversation(finished_conversation)

    @rx.event
    def delete_submisssion(self):
        """Deletes the submission for the current exercise."""
        userinfo_id: Optional[int] = self.user_id
        if self.current_exercise and userinfo_id:
            with rx.session() as session:
                exercise_result = session.exec(
                    ExerciseResult.select().where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == userinfo_id,
                    )
                ).one_or_none()

                if exercise_result:
                    if exercise_result.conversation_text == []:
                        # delete result if no conversation text is present
                        session.delete(exercise_result)
                    else:
                        exercise_result.finished_conversation = []
                        exercise_result.submit_time_stamp = None
                    session.commit()
                yield rx.toast.success(
                    title="Submission Deleted",
                    description="Your submission has been deleted successfully.",
                    duration=2500,
                    position="bottom-center",
                    invert=True,
                )
        return rx.redirect(self.chat_url)

    def set_messages_from_conversation(self, finished_conversation):
        """Parses and stores the messages."""
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
        self.exercise_title = "No Exercise Selected"
