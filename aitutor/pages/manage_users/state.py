"""State for the manage users page."""

import asyncio
import email.utils
import logging

import reflex as rx
from reflex_local_auth.auth_session import LocalAuthSession
from sqlmodel import Session, case, cast, select

import aitutor.global_vars as gv
from aitutor.account_emails import send_email_verification_email
from aitutor.auth.protection import state_require_role_or_permission
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import (
    GlobalPermission,
    Language,
    LectureRole,
    LinkUserLecture,
    LocalUser,
    Permission,
    UserInfo,
    UserRole,
)
from aitutor.verification import (
    cancel_pending_email_change,
    get_pending_email_changes,
    issue_token,
)

logger = logging.getLogger(__name__)

MANAGE_USERS_FIELD_MAX_LENGTHS: dict[str, int] = {
    "username": gv.USERNAME_MAX_LEN,
    "email": gv.EMAIL_MAX_LEN,
}


class ManageUsersState(SessionState):
    """State for managing user accounts."""

    #: Users with the address of a pending email change ("" if there is none).
    users: list[tuple[LocalUser, UserInfo, str]] = []
    edited_user: tuple[LocalUser, UserInfo] | None = None
    #: Address the edited user still has to confirm, "" if there is no pending change.
    edited_user_pending_email: str = ""
    edited_user_permissions: list[GlobalPermission] = []
    edit_dialog_is_open: bool = False
    save_in_progress: bool = False
    resend_in_progress: bool = False

    @rx.event
    @state_require_role_or_permission(
        required_role=UserRole.ADMIN,
        allowed_permissions=[GlobalPermission.MAINTAINER],
    )
    def on_load(self):
        """Initialize the state"""
        self.global_load()
        self.load_users()

    def load_users(self):
        """Load the users from the database."""
        # Define role order for sorting (based on definition order in the database enum,
        # which hopefully always matches that of UserRole).
        # Based on https://stackoverflow.com/a/23618085/2095383
        role_order_whens = {
            cast(role.name, UserInfo.role.type): role.value  # type: ignore
            for role in UserRole
        }
        role_sort_logic = case(role_order_whens, value=UserInfo.role)

        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .order_by(role_sort_logic.desc(), LocalUser.username)
            )
            pending_emails = get_pending_email_changes(session)
            self.users = [
                (lu, ui, pending_emails.get(lu.id, ""))  # type: ignore
                for lu, ui in session.exec(query).all()
            ]

    @rx.var(initial_value=False)
    def edited_user_has_admin_permission(self) -> bool:
        """Whether the edited user currently has global ADMIN permission."""
        return GlobalPermission.ADMIN in self.edited_user_permissions

    @rx.var(initial_value=False)
    def edited_user_has_maintainer_permission(self) -> bool:
        """Whether the edited user currently has MAINTAINER permission."""
        return GlobalPermission.MAINTAINER in self.edited_user_permissions

    @rx.var(initial_value=False)
    def edited_user_has_lecturer_permission(self) -> bool:
        """Whether the edited user currently has LECTURER permission."""
        return GlobalPermission.LECTURER in self.edited_user_permissions

    @rx.event
    def close_edit_dialog(self):
        """Close the edit dialog."""
        self.edit_dialog_is_open = False
        self.edited_user = None
        self.edited_user_pending_email = ""
        self.edited_user_permissions = []

    @rx.event
    def open_edit_dialog(self, user_id: int):
        """Open the edit dialog for a user."""

        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .where(LocalUser.id == user_id)
            )
            row = session.exec(query).one_or_none()

            permissions = session.exec(
                select(Permission.permission).where(Permission.user_id == user_id)
            ).all()

            pending_email = get_pending_email_changes(session, user_id=user_id).get(
                user_id, ""
            )

        if not row:
            return rx.toast.error(
                BT.error_user_not_found(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        # need to convert to proper tuple to avoid some weird type errors...
        self.edited_user = (row[0], row[1])
        self.edited_user_pending_email = pending_email
        self.edited_user_permissions = permissions  # type: ignore
        self.edit_dialog_is_open = True

    def _error_toast(self, message: str):
        """Create an error toast in the style used on this page."""
        return rx.toast.error(
            message, duration=7_000, position="bottom-center", invert=True
        )

    def _load_user(
        self, session: Session, user_id: int
    ) -> tuple[tuple[LocalUser, UserInfo] | None, str]:
        """
        Load a user together with their UserInfo.

        Returns:
            The user or None, and in the latter case an error message for the admin.
        """
        local_user = session.get(LocalUser, user_id)
        if local_user is None:
            return None, BT.error_user_not_found(self.language)

        user_info = session.exec(
            select(UserInfo).where(UserInfo.user_id == user_id)
        ).one_or_none()
        if user_info is None:
            # Every LocalUser gets a UserInfo at registration, so this means the
            # database is inconsistent.
            logger.error(
                "ERROR: No UserInfo found for user_id=%s ('%s'). The database is"
                " inconsistent.",
                user_id,
                local_user.username,
            )
            return None, BT.error_user_info_missing(self.language)

        return (local_user, user_info), ""

    def _apply_email_change(
        self, session: Session, user_info: UserInfo, new_email: str
    ) -> tuple[str | None, str | None, bool]:
        """
        Handle the email address entered in the edit form.

        - For an account that is not verified yet, the address is simply replaced and
          a new confirmation link has to be sent to it.
        - For a verified account the change is only *pending*: the old address stays
          in place until the link sent to the new address is opened (see
          `aitutor.verification.redeem_email_token`).  Entering the old address again
          discards a pending change.

        Note that the caller is responsible for committing the session.

        Args:
            session: Database session.  Not committed by this function.
            user_info: UserInfo of the edited user.
            new_email: The address entered in the form.

        Returns:
            A tuple ``(verify_email, token, cancelled)``: the address a confirmation
            link has to be sent to and the token for it (both None if no mail has to be
            sent), and whether a pending change has been discarded.
        """
        user_id = user_info.user_id

        # address a confirmation link has to be sent to, if any
        verify_email: str | None = None
        cancelled = False
        if not user_info.verified:
            # Nothing confirmed that would be worth keeping (typically the admin
            # corrects a typo from the registration), so replace it.
            if new_email != user_info.email:
                user_info.email = new_email
                verify_email = new_email
        else:
            pending_email = get_pending_email_changes(session, user_id=user_id).get(
                user_id
            )
            if new_email == user_info.email:
                cancelled = cancel_pending_email_change(session, user_id=user_id)
            elif new_email != pending_email:
                verify_email = new_email

        if verify_email is None:
            return None, None, cancelled

        token = issue_token(session, user_id=user_id, email=verify_email)
        return verify_email, token, cancelled

    async def _send_verification_email(
        self,
        *,
        user_id: int,
        to_email: str,
        username: str,
        language: Language,
        token: str,
        success_message: str,
        failure_message: str,
    ):
        """
        Send a mail with an email confirmation link to a user.

        Args:
            user_id: ID of the user, only used for logging.
            to_email: Address the mail is sent to.
            username: Name of the user, used in the mail.
            language: Language of the mail (i.e. of the user, not of the admin).
            token: The clear text verification token.
            success_message: Toast message if the mail was sent.
            failure_message: Toast message if sending the mail failed.

        Returns:
            A toast telling the admin whether the mail was sent.
        """
        try:
            await asyncio.to_thread(
                send_email_verification_email,
                to_email=to_email,
                username=username,
                language=language,
                verification_token=token,
            )
        except Exception:
            logger.exception(
                "Failed to send verification email for user_id=%s (triggered by an"
                " admin).",
                user_id,
            )
            return self._error_toast(failure_message)

        return rx.toast.success(
            success_message,
            duration=7_000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    @state_require_role_or_permission(
        required_role=UserRole.ADMIN,
        allowed_permissions=[GlobalPermission.MAINTAINER],
    )
    async def update_user(self, form_data):
        """
        Save changes to a user from the edit form.

        A changed email address has to be confirmed by the user, see
        :meth:`_apply_email_change`.
        """
        assert self.edited_user is not None
        user_id = self.edited_user[0].id
        assert user_id is not None

        # set max length for strings from UserInfo
        for field, max_length in MANAGE_USERS_FIELD_MAX_LENGTHS.items():
            if field in form_data:
                form_data[field] = form_data[field][:max_length]

        new_email = form_data["email"].strip()
        # same basic syntax check as in the registration
        if "@" not in email.utils.parseaddr(new_email, strict=True)[1]:
            yield self._error_toast(BT.error_email_invalid(self.language))
            return

        # check for the password max length in terms of bytes
        if len(form_data["new_password"].encode("utf-8")) > gv.PASSWORD_MAX_BYTES:
            yield self._error_toast(BT.error_password_too_long(self.language))
            return

        self.save_in_progress = True
        yield

        try:
            with rx.session() as session:
                row, error_message = self._load_user(session, user_id)
                if row is None:
                    yield self._error_toast(error_message)
                    return
                local_user, user_info = row
                assert local_user.id is not None

                local_user.username = form_data["username"]
                user_info.role = UserRole[form_data["role"]]

                verify_email, token, email_change_cancelled = self._apply_email_change(
                    session, user_info, new_email
                )

                if form_data["new_password"]:
                    local_user.password_hash = LocalUser.hash_password(
                        form_data["new_password"]
                    )

                # Reflex devs decided to implement checkboxes in a very smart way.
                # Instead of having a boolean true/false value, they add it with value
                # "on" in the form_data if it is checked, and do not add it at all if
                # it is not checked.
                local_user.enabled = form_data.get("enabled") == "on"

                # if user gets disabled, also end any open sessions they may still have
                if not local_user.enabled:
                    user_sessions = session.exec(
                        select(LocalAuthSession).where(
                            LocalAuthSession.user_id == local_user.id
                        )
                    ).all()
                    for us in user_sessions:
                        session.delete(us)

                selected_permissions: list[GlobalPermission] = []
                if form_data.get("global_permission_admin") == "on":
                    selected_permissions.append(GlobalPermission.ADMIN)
                if form_data.get("global_permission_maintainer") == "on":
                    selected_permissions.append(GlobalPermission.MAINTAINER)
                if form_data.get("global_permission_lecturer") == "on":
                    selected_permissions.append(GlobalPermission.LECTURER)

                existing_permissions = session.exec(
                    select(Permission).where(Permission.user_id == local_user.id)
                ).all()
                for permission in existing_permissions:
                    session.delete(permission)

                for permission in selected_permissions:
                    session.add(
                        Permission(user_id=local_user.id, permission=permission)
                    )

                # needed for the mail, read before the commit expires the objects
                username = local_user.username
                user_language = user_info.language
                is_email_change = user_info.verified

                session.commit()

            # reload users to update the table
            self.load_users()
            self.close_edit_dialog()

            if email_change_cancelled:
                yield rx.toast.info(
                    BT.admin_email_change_cancelled(self.language),
                    duration=7_000,
                    position="bottom-center",
                    invert=True,
                )

            if token is None or verify_email is None:
                return

            # let the dialog close before the (possibly slow) mail server is contacted
            yield

            yield await self._send_verification_email(
                user_id=user_id,
                to_email=verify_email,
                username=username,
                language=user_language,
                token=token,
                success_message=(
                    BT.admin_email_change_pending(self.language, verify_email)
                    if is_email_change
                    else BT.admin_verification_email_sent(self.language, verify_email)
                ),
                failure_message=BT.admin_verification_email_failed(
                    self.language, verify_email
                ),
            )
        finally:
            self.save_in_progress = False

    @rx.event
    @state_require_role_or_permission(
        required_role=UserRole.ADMIN,
        allowed_permissions=[GlobalPermission.MAINTAINER],
    )
    async def resend_verification_email_to_edited_user(self):
        """
        Send a new confirmation link to the user that is currently edited.

        The link goes to the address that still has to be confirmed: the account's
        address if it is not verified yet, otherwise the address of a pending change.
        Unlike the resend on the login page, this is not subject to the cooldown, but
        it does restart it.
        """
        if self.edited_user is None:
            return
        user_id = self.edited_user[0].id
        assert user_id is not None

        self.resend_in_progress = True
        yield

        try:
            with rx.session() as session:
                row, error_message = self._load_user(session, user_id)
                if row is None:
                    yield self._error_toast(error_message)
                    return
                local_user, user_info = row

                if not user_info.verified:
                    to_email = user_info.email
                else:
                    to_email = get_pending_email_changes(session, user_id=user_id).get(
                        user_id
                    )

                if to_email is None:
                    # Confirmed in the meantime.
                    self.edited_user_pending_email = ""
                    self.load_users()
                    yield rx.toast.info(
                        BT.admin_nothing_to_verify(self.language),
                        duration=7_000,
                        position="bottom-center",
                        invert=True,
                    )
                    return

                username = local_user.username
                user_language = user_info.language

                token = issue_token(session, user_id=user_id, email=to_email)
                # Commit before sending, same as for the resend on the login page.
                session.commit()

            yield await self._send_verification_email(
                user_id=user_id,
                to_email=to_email,
                username=username,
                language=user_language,
                token=token,
                success_message=BT.admin_verification_email_sent(
                    self.language, to_email
                ),
                failure_message=BT.verification_email_resend_failed(self.language),
            )
        finally:
            self.resend_in_progress = False

    @rx.event
    def delete_user(self, user_id: int):
        """Delete a user from the database."""
        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .where(LocalUser.id == user_id)
            )
            row = session.exec(query).one_or_none()

            if row:
                local_user, user_info = row

                owner_links = session.exec(
                    select(LinkUserLecture).where(
                        LinkUserLecture.user_id == local_user.id,
                        LinkUserLecture.role == LectureRole.OWNER,
                    )
                ).all()

                # Block deletion if the user is the sole owner of any lecture.
                for owner_link in owner_links:
                    if owner_link.lecture_id is None:
                        continue
                    other_owner = session.exec(
                        select(LinkUserLecture).where(
                            LinkUserLecture.lecture_id == owner_link.lecture_id,
                            LinkUserLecture.user_id != local_user.id,
                            LinkUserLecture.role == LectureRole.OWNER,
                        )
                    ).first()
                    if other_owner is None:
                        return rx.toast.error(
                            BT.cannot_delete_sole_lecture_owner(self.language),
                            duration=7000,
                            position="bottom-center",
                            invert=True,
                        )

                # NOTE: The deletions below could be reduced to a single delete of
                # LocalUser if delete cascades where set up properly.  However, since
                # LocalUser and LocalAuthSession are defined in the reflex_local_auth,
                # we don't have direct influence on it.

                session.delete(local_user)
                # delete does not cascade from LocalUser to UserInfo, so we need to do
                # this explicilty
                session.delete(user_info)

                # and also delete any open sessions the user may still have (doesn't
                # cascade either...)
                user_sessions = session.exec(
                    select(LocalAuthSession).where(
                        LocalAuthSession.user_id == local_user.id
                    )
                ).all()
                for us in user_sessions:
                    session.delete(us)

                session.commit()
            else:
                return rx.toast.error(
                    BT.error_user_not_found(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

        # reload the table
        self.load_users()

        return rx.toast.success(
            BT.deleted_user(self.language, local_user.username),
            duration=5000,
            position="bottom-center",
            invert=True,
        )
