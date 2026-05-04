"""State for the lecture overview page."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.models import (
    GlobalPermission,
    Lecture,
    LinkUserLecture,
    UserRole,
)


class LectureOverviewState(SessionState):
    """State for one lecture-specific overview page."""

    current_lecture_id: int | None = None
    lecture_name: str = ""
    lecturer_name: str = ""
    lecture_information_text: str = ""

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the lecture overview state when the page loads."""
        self.global_load()
        self._reset_lecture_state()

        lecture_id_param = self._get_route_lecture_id_param()
        try:
            lecture_id = int(lecture_id_param)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)
            self._apply_lecture_to_state(lecture)

    def on_logout(self):
        """Clear lecture-specific state when the user logs out."""
        self._reset_lecture_state()

    def _reset_lecture_state(self) -> None:
        """Reset all page-local state values."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.lecturer_name = ""
        self.lecture_information_text = ""

    def _apply_lecture_to_state(self, lecture: Lecture) -> None:
        """Copy the loaded lecture into state variables for rendering."""
        self.current_lecture_id = lecture.id
        self.lecture_name = lecture.lecture_name
        self.lecturer_name = lecture.lecturer_name
        self.lecture_information_text = lecture.lecture_information_text

    def _get_route_lecture_id_param(self) -> str:
        """Return the lecture id route segment."""
        return str(self.router.url.path.rstrip("/").split("/")[-1])

    def _user_may_view_lecture(self, lecture_id: int) -> bool:
        """Check whether the current user may open this lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False
        if GlobalPermission.ADMIN in self.global_permissions:
            return True

        with rx.session() as session:
            link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == lecture_id,
                    LinkUserLecture.user_id == self.authenticated_user.id,
                )
            ).one_or_none()

        return link is not None