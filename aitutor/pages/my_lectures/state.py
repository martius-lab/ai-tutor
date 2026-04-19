"""State for the my lectures page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import (
    GlobalPermission,
    Lecture,
    LinkUserLecture,
    UserRole,
)

LectureWithRole = tuple[Lecture, int]


class MyLecturesState(SessionState):
    """State for the my lectures page."""

    joined_lectures: list[LectureWithRole] = []

    @rx.var
    def can_create_lectures(self) -> bool:
        """Whether the current user may create new lectures."""
        return (
            GlobalPermission.LECTURER in self.global_permissions
            or GlobalPermission.ADMIN in self.global_permissions
        )

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the page state."""
        self.global_load()
        self.load_joined_lectures()

    def on_logout(self):
        """Clear page-specific state on logout."""
        self.joined_lectures = []

    def load_joined_lectures(self):
        """Load all lectures the current user is a member of."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            self.joined_lectures = []
            return

        with rx.session() as session:
            joined = session.exec(
                select(Lecture, LinkUserLecture.role)
                .join(LinkUserLecture)
                .where(LinkUserLecture.user_id == self.authenticated_user.id)
                .order_by(Lecture.lecture_name)
            ).all()

        self.joined_lectures = [
            (lecture, int(role))
            for lecture, role in joined  # type: ignore[arg-type]
        ]
