"""State for the edit lecture page."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import GlobalPermission, Lecture, LectureRole, LinkUserLecture


class EditLectureState(SessionState):
    """State for the edit lecture page skeleton."""

    current_lecture_id: int | None = None
    lecture_name: str = ""
    registration_code: str = ""
    lecture_information_text: str = ""
    check_conversation_prompt: str = ""
    unsaved_changes: bool = False
    is_new: bool = True
    lecture_id_param: str = "new"

    @rx.event
    def set_lecture_value(self, name: str, value: str):
        """Update one lecture field in the page state."""
        setattr(self, name, value)
        self.unsaved_changes = True

    def _user_may_edit_existing_lecture(self, lecture_id: int) -> bool:
        """Check whether the current user may edit an existing lecture."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False
        if GlobalPermission.ADMIN in self.global_permissions:
            return True

        with rx.session() as session:
            link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == lecture_id,
                    LinkUserLecture.user_id == self.authenticated_user.id,
                    LinkUserLecture.role == LectureRole.OWNER,
                )
            ).one_or_none()
        return link is not None

    @rx.event
    @state_require_role_or_permission(
        allowed_permissions=[GlobalPermission.LECTURER],
    )
    def on_load(self):
        """Initialize the page state."""
        self.global_load()
        self.unsaved_changes = False

        lecture_id_param = self.router.url.path.rstrip("/").split("/")[-1]
        if lecture_id_param == routes.EDIT_LECTURE.split("/")[-1]:
            lecture_id_param = "new"
        self.lecture_id_param = str(lecture_id_param)

        if lecture_id_param == "new":
            self.current_lecture_id = None
            self.lecture_name = ""
            self.registration_code = ""
            self.lecture_information_text = ""
            self.check_conversation_prompt = ""
            self.is_new = True
            return

        try:
            lecture_id = int(str(lecture_id_param))
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_edit_existing_lecture(lecture_id):
            return rx.redirect(routes.HOME)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)
            self.current_lecture_id = lecture.id
            self.lecture_name = lecture.lecture_name
            self.registration_code = lecture.registration_code
            self.lecture_information_text = lecture.lecture_information_text
            self.check_conversation_prompt = lecture.check_conversation_prompt
        self.is_new = False
        self.unsaved_changes = False

    def on_logout(self):
        """Clear lecture-specific state on logout."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.registration_code = ""
        self.lecture_information_text = ""
        self.check_conversation_prompt = ""
        self.unsaved_changes = False
        self.is_new = True
        self.lecture_id_param = "new"

    @rx.event
    @state_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
    def save_lecture(self):
        """Create a new lecture or save changes to an existing one."""
        if not self.lecture_name.strip():
            return rx.window_alert("Please enter a lecture name.")

        if self.authenticated_user is None or self.authenticated_user.id is None:
            return rx.redirect(routes.LOGIN)

        with rx.session() as session:
            if self.is_new:
                lecture = Lecture(
                    lecture_name=self.lecture_name,
                    registration_code=self.registration_code,
                    lecture_information_text=self.lecture_information_text,
                    check_conversation_prompt=self.check_conversation_prompt,
                )
                session.add(lecture)
                session.commit()
                session.refresh(lecture)

                session.add(
                    LinkUserLecture(
                        lecture_id=lecture.id,
                        user_id=self.authenticated_user.id,
                        role=LectureRole.OWNER,
                    )
                )
                session.commit()

                self.current_lecture_id = lecture.id
                self.lecture_name = lecture.lecture_name
                self.registration_code = lecture.registration_code
                self.lecture_information_text = lecture.lecture_information_text
                self.check_conversation_prompt = lecture.check_conversation_prompt
                self.is_new = False
                self.lecture_id_param = str(lecture.id)
                self.unsaved_changes = False

                return [
                    rx.toast.success(
                        description=BT.changes_saved(self.language),
                        duration=5000,
                        position="bottom-center",
                        invert=True,
                    ),
                    rx.redirect(f"{routes.EDIT_LECTURE}/{lecture.id}"),
                ]

            lecture_id = self.current_lecture_id
            if lecture_id is None:
                return rx.redirect(routes.NOT_FOUND)

            if not self._user_may_edit_existing_lecture(lecture_id):
                return rx.redirect(routes.HOME)

            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)

            lecture.lecture_name = self.lecture_name
            lecture.registration_code = self.registration_code
            lecture.lecture_information_text = self.lecture_information_text
            lecture.check_conversation_prompt = self.check_conversation_prompt
            session.add(lecture)
            session.commit()
            session.refresh(lecture)
            self.current_lecture_id = lecture.id
            self.lecture_name = lecture.lecture_name
            self.registration_code = lecture.registration_code
            self.lecture_information_text = lecture.lecture_information_text
            self.check_conversation_prompt = lecture.check_conversation_prompt

        self.unsaved_changes = False
        return rx.toast.success(
            description=BT.changes_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )
