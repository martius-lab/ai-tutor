"""State for the all lectures page."""

from collections.abc import Sequence

import reflex as rx
from sqlmodel import and_, select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Lecture, LectureRole, LinkUserLecture, UserRole

LectureWithRole = tuple[Lecture, int | None]


class AllLecturesState(SessionState):
    """State for browsing all lectures."""

    lectures: list[LectureWithRole] = []
    search_text: str = ""
    expanded_lecture_id: int | None = None
    join_dialog_is_open: bool = False
    selected_lecture_id: int | None = None
    selected_lecture_name: str = ""
    selected_lecture_registration_code: str = ""
    selected_lecture_lecturer_name: str = ""
    entered_registration_code: str = ""
    lecture_id_param: str = ""

    @rx.event
    def update_search_text(self, value: str):
        """Update the lecture search text."""
        self.search_text = value

    @rx.event
    def set_entered_registration_code(self, value: str):
        """Update the entered registration code for the join dialog."""
        self.entered_registration_code = value

    @rx.event
    def toggle_lecture_details(self, lecture_id: int):
        """Toggle whether lecture details are expanded."""
        if self.expanded_lecture_id == lecture_id:
            self.expanded_lecture_id = None
            return

        self.expanded_lecture_id = lecture_id

    @rx.event
    def open_join_dialog(self, lecture_id: int):
        """Prepare and open the join dialog for a loaded lecture."""
        lecture_with_role = self._find_loaded_lecture(lecture_id)
        if lecture_with_role is None:
            return rx.toast.error(
                description=BT.lecture_not_found(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        lecture = lecture_with_role[0]

        self.selected_lecture_id = lecture_id
        self.selected_lecture_name = lecture.lecture_name
        self.selected_lecture_registration_code = lecture.registration_code
        self.selected_lecture_lecturer_name = lecture.lecturer_name
        self.entered_registration_code = ""
        self.join_dialog_is_open = True

    @rx.event
    def close_join_dialog(self):
        """Close the join dialog and clear its local state."""
        self._reset_join_dialog()

    @rx.event
    def set_join_dialog_is_open(self, value: bool):
        """Open or close the join dialog from the dialog component."""
        if value:
            self.join_dialog_is_open = True
            return

        self.close_join_dialog()

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def join_selected_lecture(self):
        """Validate the selected lecture and join it as a student."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return

        lecture_id = self.selected_lecture_id
        if lecture_id is None:
            return rx.toast.error(
                description=BT.lecture_not_found(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.toast.error(
                    description=BT.lecture_not_found(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            existing_link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == lecture_id,
                    LinkUserLecture.user_id == self.authenticated_user.id,
                )
            ).one_or_none()
            if existing_link is not None:
                return rx.toast.error(
                    description=BT.already_joined_lecture(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            if lecture.registration_code and (
                self.entered_registration_code != lecture.registration_code
            ):
                return rx.toast.error(
                    description=BT.invalid_lecture_registration_code(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            session.add(
                LinkUserLecture(
                    lecture_id=lecture_id,
                    user_id=self.authenticated_user.id,
                    role=LectureRole.STUDENT,
                )
            )
            session.commit()

        self.load_lectures()
        self.close_join_dialog()
        return rx.toast.success(
            description=BT.joined_lecture_successfully(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the page state."""
        self.global_load()
        self._reset_page_state()
        self.load_lectures()

        lecture_id_param = self._get_route_lecture_id_param()
        self.lecture_id_param = lecture_id_param
        if not lecture_id_param:
            return

        try:
            lecture_id = int(lecture_id_param)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        return self.open_join_dialog(lecture_id)

    def on_logout(self):
        """Clear page-specific state on logout."""
        self.lectures = []
        self._reset_page_state()

    @rx.var
    def filtered_lectures(self) -> list[LectureWithRole]:
        """Return loaded lectures filtered locally by the search text."""
        search_text = self.search_text.strip().lower()
        if not search_text:
            return self.lectures

        return [
            (lecture, role)
            for lecture, role in self.lectures
            if search_text in lecture.lecture_name.lower()
        ]

    @rx.var
    def selected_lecture_requires_code(self) -> bool:
        """Whether the currently selected lecture requires a registration code."""
        return bool(self.selected_lecture_registration_code)

    @rx.var
    def can_join_selected_lecture(self) -> bool:
        """Whether the user has entered all required join information."""
        if self.selected_lecture_id is None:
            return False
        if not self.selected_lecture_requires_code:
            return True
        return bool(self.entered_registration_code)

    def _reset_page_state(self) -> None:
        """Reset local page UI state without clearing loaded lectures."""
        self.search_text = ""
        self.expanded_lecture_id = None
        self._reset_join_dialog()

    def _reset_join_dialog(self) -> None:
        """Reset the join dialog and its selected lecture data."""
        self.join_dialog_is_open = False
        self.selected_lecture_id = None
        self.selected_lecture_name = ""
        self.selected_lecture_registration_code = ""
        self.selected_lecture_lecturer_name = ""
        self.entered_registration_code = ""

    def _find_loaded_lecture(self, lecture_id: int) -> LectureWithRole | None:
        """Find a lecture in the already loaded list without querying the database."""
        return next(
            (
                lecture_with_role
                for lecture_with_role in self.lectures
                if lecture_with_role[0].id == lecture_id
            ),
            None,
        )

    def _serialize_lectures(
        self,
        lectures: Sequence[tuple[Lecture, int | None]],
    ) -> list[LectureWithRole]:
        """Convert raw query results to state-friendly tuples."""
        return [
            (
                lecture,
                int(role) if role is not None else None,
            )
            for lecture, role in lectures
        ]

    def load_lectures(self):
        """Load all lectures and the current user's role for each lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            self.lectures = []
            return

        with rx.session() as session:
            lectures = session.exec(
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

        self.lectures = self._serialize_lectures(lectures)

    def _get_route_lecture_id_param(self) -> str:
        """Return the lecture id route segment or an empty string."""
        path_segments = self.router.url.path.rstrip("/").split("/")
        last_segment = path_segments[-1]
        if last_segment == routes.ALL_LECTURES.split("/")[-1]:
            return ""
        return str(last_segment)

