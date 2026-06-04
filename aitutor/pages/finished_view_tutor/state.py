"""The state for the finished view page."""

from typing import Optional

import reflex as rx
from reflex_local_auth import LocalUser
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import Exercise, ExerciseResult, UserInfo, UserRole
from aitutor.pages.chat.state import ChatMessage, Role
from aitutor.utilities.lecture_permissions import user_may_view_lecture_submissions


class FinishedViewTutorState(SessionState):
    """The State for the finished view."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    username: str
    exercise_title: str = "No Exercise Selected"
    current_lecture_id: int | None = None

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Loads the finished exercise and user info."""

        self.global_load()
        self.current_lecture_id = None
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
                return

            exercise, username, finished_conversation = result  # type: ignore
            if not self._user_may_view_submission(exercise):
                yield rx.redirect(routes.MY_LECTURES)
                return

            self.current_exercise = exercise
            self.current_lecture_id = exercise.lecture_id
            self.exercise_title = exercise.title
            self.username = username
            self.messages = []
            self.set_messages_from_conversation(finished_conversation)

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.messages = []
        self.current_exercise = None
        self.username = ""
        self.exercise_title = "No Exercise Selected"
        self.current_lecture_id = None

    @rx.var
    def submissions_url(self) -> str:
        """Return to the matching global or lecture-specific submissions page."""
        if self.current_lecture_id is not None:
            return f"{routes.LECTURE_SUBMISSIONS}/{self.current_lecture_id}"
        return routes.SUBMISSIONS

    def _user_may_view_submission(self, exercise: Exercise) -> bool:
        """Return whether the current user may view this submitted exercise."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        if exercise.lecture_id is None:
            return self.is_global_admin or (
                self.user_role is not None and self.user_role >= UserRole.TUTOR
            )

        with rx.session() as session:
            return user_may_view_lecture_submissions(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=exercise.lecture_id,
            )

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
