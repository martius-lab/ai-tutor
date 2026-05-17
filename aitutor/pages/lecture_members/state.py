"""State for the lecture members page."""

from dataclasses import dataclass

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import (
    GlobalPermission,
    Lecture,
    LectureRole,
    LinkUserLecture,
    UserRole,
)


@dataclass
class LectureMemberRow:
    """Serializable row data for one lecture member."""

    user_id: int
    username: str
    role: str
    selected_role: str


class LectureMembersState(SessionState):
    """State for listing all members of one lecture."""

    current_lecture_id: int | None = None
    lecture_name: str = ""
    members: list[LectureMemberRow] = []
    current_user_lecture_role: int | None = None

    @rx.event
    def set_member_role(self, user_id: int, role_name: str):
        """Update the selected role for one loaded member."""
        self.members = [
            LectureMemberRow(
                user_id=member.user_id,
                username=member.username,
                role=member.role,
                selected_role=role_name
                if member.user_id == user_id
                else member.selected_role,
            )
            for member in self.members
        ]

    @rx.event
    def cancel_member_role_change(self, user_id: int):
        """Reset one selected role to the persisted role."""
        self.members = [
            LectureMemberRow(
                user_id=member.user_id,
                username=member.username,
                role=member.role,
                selected_role=member.role
                if member.user_id == user_id
                else member.selected_role,
            )
            for member in self.members
        ]

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def save_member_role_change(self, user_id: int):
        """Persist one changed lecture member role."""
        if not self.can_manage_members or self.current_lecture_id is None:
            return

        changed_member = self._find_member(user_id)
        if (
            changed_member is None
            or changed_member.role == changed_member.selected_role
        ):
            return

        if self._would_remove_last_owner(
            changed_member,
            new_role=changed_member.selected_role,
        ):
            return self._sole_owner_error_toast()

        with rx.session() as session:
            link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == self.current_lecture_id,
                    LinkUserLecture.user_id == user_id,
                )
            ).one_or_none()
            if link is None:
                return

            link.role = LectureRole[changed_member.selected_role]
            session.commit()

        self.load_members()

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def kick_member(self, user_id: int):
        """Remove one member from the current lecture."""
        if not self.can_manage_members or self.current_lecture_id is None:
            return

        member = self._find_member(user_id)
        if member is None:
            return

        if self._would_remove_last_owner(member):
            return self._sole_owner_error_toast()

        with rx.session() as session:
            link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == self.current_lecture_id,
                    LinkUserLecture.user_id == user_id,
                )
            ).one_or_none()
            if link is None:
                return

            session.delete(link)
            session.commit()

        self.load_members()

    @rx.event
    @state_require_role_or_permission(required_role=UserRole.STUDENT)
    def on_load(self):
        """Initialize the members page."""
        self.global_load()
        self._reset_page_state()

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return rx.redirect(routes.NOT_FOUND)

        if not self._user_may_view_lecture(lecture_id):
            return rx.redirect(routes.MY_LECTURES)

        with rx.session() as session:
            lecture = session.get(Lecture, lecture_id)
            if lecture is None:
                return rx.redirect(routes.NOT_FOUND)

            self.current_lecture_id = lecture.id
            self.lecture_name = lecture.lecture_name

        self.load_members()

    def on_logout(self):
        """Clear page-specific state on logout."""
        self._reset_page_state()

    @rx.var
    def is_owner(self) -> bool:
        """Whether the current user is an owner of this lecture."""
        return self.current_user_lecture_role == LectureRole.OWNER.value

    @rx.var
    def can_manage_members(self) -> bool:
        """Whether the current user may manage members of this lecture."""
        return self.is_global_admin or self.is_owner

    def _reset_page_state(self) -> None:
        """Reset loaded lecture and member data."""
        self.current_lecture_id = None
        self.lecture_name = ""
        self.members = []
        self.current_user_lecture_role = None

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

    def load_members(self):
        """Load all members for the current lecture."""
        if self.current_lecture_id is None:
            self.members = []
            return

        with rx.session() as session:
            rows = session.exec(
                select(LocalUser, LinkUserLecture.role)
                .join(LinkUserLecture)
                .where(LinkUserLecture.lecture_id == self.current_lecture_id)
                .order_by(LocalUser.username)
            ).all()

        self.members = [
            LectureMemberRow(
                user_id=int(user.id),
                username=user.username,
                role=LectureRole(int(role)).name,
                selected_role=LectureRole(int(role)).name,
            )
            for user, role in rows
            if user.id is not None
        ]
        self.members.sort(
            key=lambda member: (
                -LectureRole[member.role].value,
                member.username.lower(),
            )
        )
        self.current_user_lecture_role = self._find_current_user_role()

    def _find_current_user_role(self) -> int | None:
        """Return the loaded lecture role for the authenticated user."""
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return None
        for member in self.members:
            if member.user_id == self.authenticated_user.id:
                return LectureRole[member.role].value
        return None

    def _find_member(self, user_id: int) -> LectureMemberRow | None:
        """Return one loaded member by user id."""
        return next(
            (member for member in self.members if member.user_id == user_id),
            None,
        )

    def _would_remove_last_owner(
        self,
        member: LectureMemberRow,
        *,
        new_role: str | None = None,
    ) -> bool:
        """Return whether an action would leave the lecture without an owner."""
        if member.role != LectureRole.OWNER.name:
            return False
        if new_role == LectureRole.OWNER.name:
            return False
        return self._owner_count() <= 1

    def _sole_owner_error_toast(self):
        """Show a toast for actions that would remove the last lecture owner."""
        return rx.toast.error(
            BT.cannot_remove_sole_lecture_owner(self.language),
            duration=7000,
            position="bottom-center",
            invert=True,
        )

    def _owner_count(self) -> int:
        """Return the number of loaded owners."""
        return sum(
            1 for member in self.members if member.role == LectureRole.OWNER.name
        )
