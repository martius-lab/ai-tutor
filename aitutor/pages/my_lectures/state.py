"""State for the my lectures page."""

from collections.abc import Sequence

import reflex as rx
from sqlmodel import and_, select

from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import (
    GlobalPermission,
    Lecture,
    LectureRole,
    LinkUserLecture,
    UserRole,
)

LectureWithRole = tuple[Lecture, int | None]


class MyLecturesState(SessionState):
    """State for the my lectures page."""

    joined_lectures: list[LectureWithRole] = []
    search_text: str = ""
    role_filter: str = "all"

    def _reset_filters(self) -> None:
        """Reset the local filters and loaded lectures."""
        self.joined_lectures = []
        self.search_text = ""
        self.role_filter = "all"

    def _normalized_search_text(self) -> str:
        """Return the normalized search text used for lecture filtering."""
        return self.search_text.strip().lower()

    def _matches_search_text(self, lecture: Lecture, search_text: str) -> bool:
        """Return whether a lecture matches the current search text."""
        return search_text in lecture.lecture_name.lower()

    def _matches_role_filter(self, role: int | None) -> bool:
        """Return whether a lecture role matches the selected role filter."""
        if self.role_filter == "all":
            return True
        if self.role_filter == "owner":
            return role == LectureRole.OWNER.value
        if self.role_filter == "tutor":
            return role == LectureRole.TUTOR.value
        if self.role_filter == "student":
            return role == LectureRole.STUDENT.value
        if self.role_filter == "not_joined":
            return role is None
        return True

    def _serialize_joined_lectures(
        self,
        joined: Sequence[tuple[Lecture, int | LectureRole | None]],
    ) -> list[LectureWithRole]:
        """Convert raw query results to the state-friendly lecture/role tuples."""
        return [
            (lecture, int(role) if role is not None else None)
            for lecture, role in joined
        ]

    @rx.var
    def is_global_admin(self) -> bool:
        """Whether the current user is a global admin."""
        return GlobalPermission.ADMIN in self.global_permissions

    @rx.var
    def filtered_lectures(self) -> list[LectureWithRole]:
        """Return lectures filtered by search text and role."""
        search_text = self._normalized_search_text()
        lectures = self.joined_lectures

        if search_text:
            lectures = [
                (lecture, role)
                for lecture, role in lectures
                if self._matches_search_text(lecture, search_text)
            ]

        return [
            (lecture, role)
            for lecture, role in lectures
            if self._matches_role_filter(role)
        ]

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
        self._reset_filters()

    @rx.event
    def update_search_text(self, value: str):
        """Update the lecture name search text."""
        self.search_text = value

    @rx.event
    def set_role_filter(self, value: str):
        """Set the role filter."""
        self.role_filter = value

    def load_joined_lectures(self):
        """Load all lectures visible to the current user."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            self.joined_lectures = []
            return

        with rx.session() as session:
            if self.is_global_admin:
                joined = session.exec(
                    select(Lecture, LinkUserLecture.role)
                    .join(
                        LinkUserLecture,
                        and_(
                            LinkUserLecture.lecture_id == Lecture.id,
                            LinkUserLecture.user_id == self.authenticated_user.id,
                        ),
                        isouter=True,
                    )
                    .order_by(Lecture.lecture_name)
                ).all()
            else:
                joined = session.exec(
                    select(Lecture, LinkUserLecture.role)
                    .join(LinkUserLecture)
                    .where(LinkUserLecture.user_id == self.authenticated_user.id)
                    .order_by(Lecture.lecture_name)
                ).all()

        self.joined_lectures = self._serialize_joined_lectures(joined)
