"""State for the edit lecture page."""

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.global_vars import DEFAULT_CHECK_CONVERSATION_PROMPT
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
    delete_confirmation_password: str = ""

    @rx.event
    def set_lecture_value(self, name: str, value: str):
        """Update one editable lecture field and mark the form as changed."""
        setattr(self, name, value)
        self.unsaved_changes = True

    @rx.event
    def set_delete_confirmation_password(self, value: str):
        """Update the password used to confirm lecture deletion."""
        self.delete_confirmation_password = value

    @rx.event
    def clear_delete_confirmation_password(self):
        """Clear the password used to confirm lecture deletion."""
        self.delete_confirmation_password = ""

    @rx.event
    @state_require_role_or_permission(
        allowed_permissions=[GlobalPermission.LECTURER],
    )
    def on_load(self):
        """Initialize the page state."""
        self.global_load()
        lecture_id_param = self._get_route_lecture_id_param()
        self.lecture_id_param = lecture_id_param

        if lecture_id_param == "new":
            self._reset_form(
                check_conversation_prompt=DEFAULT_CHECK_CONVERSATION_PROMPT,
            )
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
            self._apply_lecture_to_state(lecture)

    def on_logout(self):
        """Clear lecture-specific state on logout."""
        self._reset_form()
        self.lecture_id_param = "new"
        self.delete_confirmation_password = ""

    @rx.event
    @state_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
    def save_lecture(self):
        """Create a new lecture or save changes to an existing one."""
        lecture_name = self._normalized_lecture_name()
        if not lecture_name:
            return rx.window_alert(BT.enter_lecture_name(self.language))

        if self.authenticated_user is None or self.authenticated_user.id is None:
            return rx.redirect(routes.LOGIN)

        with rx.session() as session:
            existing_lecture = session.exec(
                select(Lecture).where(Lecture.lecture_name == lecture_name)
            ).one_or_none()

            if self.is_new:
                if existing_lecture is not None:
                    return rx.toast.error(
                        description=BT.lecture_name_already_exists(self.language),
                        duration=5000,
                        position="bottom-center",
                        invert=True,
                    )

                lecture = Lecture(
                    lecture_name=lecture_name,
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

                self._apply_lecture_to_state(lecture)
                self.lecture_id_param = str(lecture.id)

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

            if existing_lecture is not None and existing_lecture.id != lecture_id:
                return rx.toast.error(
                    description=BT.lecture_name_already_exists(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            if not self._user_may_edit_existing_lecture(lecture_id):
                return rx.redirect(routes.HOME)

            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)

            self._apply_state_to_lecture(lecture, lecture_name=lecture_name)
            session.add(lecture)
            session.commit()
            session.refresh(lecture)
            self._apply_lecture_to_state(lecture)

        self.unsaved_changes = False
        return rx.toast.success(
            description=BT.changes_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    @state_require_role_or_permission(allowed_permissions=[GlobalPermission.LECTURER])
    def delete_current_lecture(self):
        """Delete the current lecture after password confirmation."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return rx.redirect(routes.LOGIN)

        lecture_id = self.current_lecture_id
        if lecture_id is None or self.is_new:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_edit_existing_lecture(lecture_id):
            return rx.redirect(routes.HOME)

        if not self.authenticated_user.verify(self.delete_confirmation_password):
            self.delete_confirmation_password = ""
            return rx.toast.error(
                description=BT.invalid_password(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)

            session.delete(lecture)
            session.commit()

        self._reset_form()
        self.lecture_id_param = "new"
        self.delete_confirmation_password = ""
        return [
            rx.toast.success(
                description=BT.lecture_deleted_successfully(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            ),
            rx.redirect(routes.MY_LECTURES),
        ]

    def _reset_form(self, *, check_conversation_prompt: str = "") -> None:
        """Reset the editable form fields to their default values."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.registration_code = ""
        self.lecture_information_text = ""
        self.check_conversation_prompt = check_conversation_prompt
        self.is_new = True
        self.unsaved_changes = False
        self.delete_confirmation_password = ""

    def _apply_lecture_to_state(self, lecture: Lecture) -> None:
        """Copy persisted lecture values into the page state."""
        self.current_lecture_id = lecture.id
        self.lecture_name = lecture.lecture_name
        self.registration_code = lecture.registration_code
        self.lecture_information_text = lecture.lecture_information_text
        self.check_conversation_prompt = lecture.check_conversation_prompt
        self.is_new = False
        self.unsaved_changes = False

    def _apply_state_to_lecture(self, lecture: Lecture, *, lecture_name: str) -> None:
        """Write the current form values into a Lecture model instance."""
        lecture.lecture_name = lecture_name
        lecture.registration_code = self.registration_code
        lecture.lecture_information_text = self.lecture_information_text
        lecture.check_conversation_prompt = self.check_conversation_prompt

    def _get_route_lecture_id_param(self) -> str:
        """Return the lecture id route segment or 'new' for the create page."""
        lecture_id_param = self.router.url.path.rstrip("/").split("/")[-1]
        if lecture_id_param == routes.EDIT_LECTURE.split("/")[-1]:
            return "new"
        return str(lecture_id_param)

    def _normalized_lecture_name(self) -> str:
        """Return the trimmed lecture name used for validation and persistence."""
        return self.lecture_name.strip()

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
