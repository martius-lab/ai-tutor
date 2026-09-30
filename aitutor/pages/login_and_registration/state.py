"""State for the login and for the registration page."""

import asyncio
import email.utils
import logging
import re
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import reflex as rx
import reflex_local_auth
from reflex_local_auth.user import LocalUser
from sqlmodel import func, select

import aitutor.global_vars as gv
from aitutor.account_emails import (
    send_email_verification_email,
    send_signup_welcome_email,
)
from aitutor.config import get_config
from aitutor.language_state import BackendTranslations as BT
from aitutor.language_state import language_from_value
from aitutor.models import (
    GlobalPermission,
    Language,
    LecturerRegistrationToken,
    Permission,
    UserInfo,
    UserRole,
)
from aitutor.verification import issue_token, resend_cooldown_remaining

# check for the password max length in terms of bytes
# alongside basic matching check against the DB
_origin_verify = LocalUser.verify
LocalUser.verify = lambda self, secret: (
    len(secret.encode("utf-8")) <= gv.PASSWORD_MAX_BYTES
    and _origin_verify(self, secret)
)

logger = logging.getLogger(__name__)

AUTH_FIELD_MAX_LENGTHS: dict[str, int] = {
    "username": gv.USERNAME_MAX_LEN,
    "email": gv.EMAIL_MAX_LEN,
    "registration_code": gv.REGISTRATION_CODE_MAX_LEN,
}


class MyLoginState(reflex_local_auth.LoginState):
    """
    A custom login state class that handles user login.
    """

    #: Whether the last login attempt failed *only* because the email address of the
    #: account has not been confirmed yet.  Controls the resend offer on the login page.
    email_not_verified: bool = False
    resend_in_progress: bool = False

    #: ID of the account of the last login attempt that failed due to a missing email
    #: confirmation.
    _unverified_user_id: int = -1
    #: Language of the login form, used for the toasts of the resend action.  This state
    #: is not a substate of SessionState, so it has no `language` of its own.
    _language: Language = Language.EN

    @rx.event
    def on_load(self):
        """function that gets called when the login page loads"""
        self.error_message = ""
        self._reset_verification_state()

    def _reset_verification_state(self):
        """Forget about a previous login attempt with an unconfirmed address."""
        self.email_not_verified = False
        self.resend_in_progress = False
        self._unverified_user_id = -1

    @rx.event
    def on_submit(self, form_data: dict[str, Any]):
        """
        Handle the login form submission.

        This replaces the handler of the base class, which does not know about the
        email confirmation.  A user may only log in if the account is enabled *and*
        the email address has been confirmed.

        Args:
            form_data: A dict of the form fields and their values.
        """
        self.error_message = ""
        self._reset_verification_state()
        self._language = language_from_value(form_data.get("language"))

        username = form_data["username"]
        password = form_data["password"]

        with rx.session() as session:
            user = session.exec(
                select(LocalUser).where(LocalUser.username == username)
            ).one_or_none()

            # Check the credentials before anything else.  Everything below reveals
            # something about the account, and the password is what earns the right to
            # learn it.
            if (
                user is None
                or user.id is None
                or not password
                or not user.verify(password)
            ):
                self.error_message = BT.login_failed(self._language)
                return rx.set_value("password", "")

            if not user.enabled:
                self.error_message = BT.account_disabled(self._language)
                return rx.set_value("password", "")

            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == user.id)
            ).one_or_none()

            if user_info is None:
                # Every LocalUser gets a UserInfo at registration, so this means the
                # database is inconsistent.  Not something the user can do anything
                # about (in particular, offering a resend would be pointless: there is
                # no address to send to), so log it for the operators and stop here.
                logger.error(
                    "ERROR: No UserInfo found for user_id=%s ('%s'). The database is"
                    " inconsistent, login is not possible for this account.",
                    user.id,
                    user.username,
                )
                self.error_message = BT.error_account_data_inconsistent(self._language)
                return rx.set_value("password", "")

            if not user_info.verified:
                # Do not log the user in, but offer to send a new confirmation mail.
                self.email_not_verified = True
                self._unverified_user_id = user.id
                return rx.set_value("password", "")

            user_info.last_login_at = datetime.now(ZoneInfo(gv.TIME_ZONE))
            session.add(user_info)
            session.commit()

            user_id = user.id

        # mark the user as logged in
        self._login(user_id)
        self.error_message = ""
        # Use the handler of the base class here: `redirect_to` is set on it by
        # `reflex_local_auth.require_login`.
        return reflex_local_auth.LoginState.redir()  # type: ignore

    @rx.event
    async def resend_verification_email(self):
        """
        Send a new confirmation mail to the account of the last login attempt.

        Only available directly after a login attempt that failed because the address
        was not confirmed, i.e. only to someone who knows the password.
        """
        if self._unverified_user_id < 0:
            return

        self.resend_in_progress = True
        yield

        try:
            with rx.session() as session:
                row = session.exec(
                    select(LocalUser, UserInfo)
                    .join(UserInfo)
                    .where(LocalUser.id == self._unverified_user_id)
                ).one_or_none()

                if row is None:
                    self._reset_verification_state()
                    yield rx.toast.error(
                        BT.error_user_not_found(self._language),
                        duration=7_000,
                        position="bottom-center",
                        invert=True,
                    )
                    return

                local_user, user_info = row
                assert local_user.id is not None

                if user_info.verified:
                    # Confirmed in the meantime, e.g. in another browser tab.
                    self._reset_verification_state()
                    yield rx.toast.info(
                        BT.email_already_verified(self._language),
                        duration=7_000,
                        position="bottom-center",
                        invert=True,
                    )
                    return

                remaining = resend_cooldown_remaining(session, user_id=local_user.id)
                if remaining > timedelta(0):
                    yield rx.toast.warning(
                        BT.verification_email_resend_cooldown(
                            self._language, seconds=int(remaining.total_seconds())
                        ),
                        duration=7_000,
                        position="bottom-center",
                        invert=True,
                    )
                    return

                username = local_user.username
                to_email = user_info.email
                user_language = user_info.language

                token = issue_token(session, user_id=local_user.id, email=to_email)
                # Commit before sending: this starts the cooldown, so a mail server that
                # is slow or broken cannot be used to send a burst of mails.  The price
                # is that a failed send makes the user wait for the next attempt.
                session.commit()

            try:
                await asyncio.to_thread(
                    send_email_verification_email,
                    to_email=to_email,
                    username=username,
                    language=user_language,
                    verification_token=token,
                )
            except Exception:
                logger.exception(
                    "Failed to resend verification email for user_id=%s.",
                    self._unverified_user_id,
                )
                yield rx.toast.error(
                    BT.verification_email_resend_failed(self._language),
                    duration=7_000,
                    position="bottom-center",
                    invert=True,
                )
                return

            yield rx.toast.success(
                BT.verification_email_resent(self._language),
                duration=7_000,
                position="bottom-center",
                invert=True,
            )
        finally:
            self.resend_in_progress = False


class MyRegisterState(reflex_local_auth.RegistrationState):
    """
    A custom registration state class that handles user registration.
    """

    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    registration_code: str = ""
    welcome_email_failed: bool = False
    registration_in_progress: bool = False

    #: Whether a registration code is required for registration.
    needs_registration_code: bool = False

    lecturer_registration_token: str = ""
    has_invalid_registration_token: bool = False

    @rx.event
    def set_username(self, value: str):
        """Set the username."""
        self.username = value[: AUTH_FIELD_MAX_LENGTHS["username"]]

    @rx.event
    def set_email(self, value: str):
        """Set the email."""
        self.email = value[: AUTH_FIELD_MAX_LENGTHS["email"]]

    @rx.event
    def set_password(self, value: str):
        """Set the password."""
        self.password = value

    @rx.event
    def set_confirm_password(self, value: str):
        """Set the confirm password."""
        self.confirm_password = value

    @rx.event
    def set_registration_code(self, value: str):
        """Set the registration code."""
        self.registration_code = value[: AUTH_FIELD_MAX_LENGTHS["registration_code"]]

    @rx.event
    def on_load(self):
        """function that gets called when the register page loads"""
        self.clear_state_vars()
        self.error_message = ""
        self.success = False
        self.needs_registration_code = bool(get_config().registration_code)

        # Important: Clear the token to prevent a previous value from being used even if
        # the current URL does not contain a token.
        self.lecturer_registration_token = ""
        self.has_invalid_registration_token = False

        lecturer_registration_token = self.router.url.query_parameters.get("lrt", "")
        if lecturer_registration_token:
            if self._validate_lecturer_registration_token(lecturer_registration_token):
                self.lecturer_registration_token = lecturer_registration_token
            else:
                self.has_invalid_registration_token = True

    def clear_state_vars(self):
        """Clear the state variables."""
        self.username = ""
        self.email = ""
        self.password = ""
        self.confirm_password = ""
        self.registration_code = ""
        self.welcome_email_failed = False
        self.registration_in_progress = False
        self.needs_registration_code = False

    # This event handler must be named something besides `handle_registration`!!!
    @rx.event
    async def handle_custom_registration(self, form_data):
        """
        Handles the registration process for a user using their email.

        Args:
            form_data (dict): A dictionary containing the user's registration data.

        Returns:
            Any: The result of the registration process.
        """
        self.registration_in_progress = True
        self.success = False
        self.welcome_email_failed = False
        self.error_message = ""
        yield

        try:
            # set the max length of the strings
            for field, max_len in AUTH_FIELD_MAX_LENGTHS.items():
                if field in form_data and isinstance(form_data[field], str):
                    form_data[field] = form_data[field][:max_len]

            language = language_from_value(form_data.get("language"))
            # check for allowed user name
            if not re.match(r"^[a-zA-Z0-9._-]+$", form_data["username"]):
                self.error_message = (
                    "Username can only contain letters, numbers and '. _ -'"
                )
                self.username = ""
                return

            # Very basic email syntax validation, mostly to catch erroneous user input.
            # For a somewhat valid email address, parseaddr returns the address as
            # second element of a tuple.  In addition, we check if there is at least an
            # '@' in it.  For a syntactically invalid email address, parseaddr returns
            # an empty string, thus always making the '@' in ...' check fail in this
            # case.
            if "@" not in email.utils.parseaddr(form_data["email"], strict=True)[1]:
                self.error_message = "Email address is not valid."
                self.email = ""
                return

            # check for the password max length in terms of bytes
            if len(form_data["password"].encode("utf-8")) > gv.PASSWORD_MAX_BYTES:
                self.error_message = BT.error_password_too_long(language)
                return

            # check for the correct registration code
            registration_code = get_config().registration_code
            if (
                registration_code
                and form_data["registration_code"] != registration_code
            ):
                self.error_message = "The registration code is wrong."
                self.registration_code = ""
                return

            registration_result = self.handle_registration(form_data)
            if self.new_user_id < 0:
                yield registration_result
                return

            with rx.session() as session:
                user_info = UserInfo(
                    email=form_data["email"],
                    role=UserRole.STUDENT,
                    user_id=self.new_user_id,
                    language=language,
                )
                session.add(user_info)

                # if valid 'lecturer registration token' is provided, assign the
                # 'lecturer' permission
                lecturer_registration_token = form_data.get(
                    "lecturer_registration_token"
                )
                if (
                    lecturer_registration_token
                    and self._validate_lecturer_registration_token(
                        lecturer_registration_token
                    )
                ):
                    session.add(
                        Permission(
                            user_id=self.new_user_id,
                            permission=GlobalPermission.LECTURER,
                        )
                    )
                    # log the usage of the lecturer registration token (makes it easier
                    # to analyse potential abuse)
                    print(
                        f"User {form_data['username']} ({self.new_user_id}) registered"
                        f" as lecturer using token {lecturer_registration_token}."
                    )

                # The account cannot be used before the address is confirmed, so
                # the token is created together with the account.
                verification_token = issue_token(
                    session,
                    user_id=self.new_user_id,
                    email=user_info.email,
                )

                session.commit()
                session.refresh(user_info)

                local_user = session.get(LocalUser, self.new_user_id)
                username = local_user.username if local_user else None

            welcome_email_sent = False
            try:
                if not username:
                    raise RuntimeError(
                        f"No LocalUser found for user_id={self.new_user_id}."
                    )
                await asyncio.to_thread(
                    send_signup_welcome_email,
                    to_email=user_info.email,
                    username=username,
                    language=user_info.language,
                    verification_token=verification_token,
                )
                welcome_email_sent = True
            except Exception:
                logger.exception(
                    "Failed to send signup welcome email for user_id=%s.",
                    self.new_user_id,
                )

            self.clear_state_vars()
            self.welcome_email_failed = not welcome_email_sent

            # Note that `registration_result` (the `successful_registration` handler
            # of the base class) is deliberately not yielded here: it would redirect to
            # the login page, but the account cannot be used until the email address is
            # confirmed, so the user better stays here and reads the message above.
            # That handler would also have reset `error_message`, `new_user_id` and set
            # `success`, so do it here instead.
            self.error_message = ""
            self.new_user_id = -1
            self.success = True
        finally:
            self.registration_in_progress = False

    def _validate_lecturer_registration_token(self, token: str) -> bool:
        """
        Check whether the given lecturer registration token exists and hasn't expired.

        Args:
            token: The lecturer registration token to validate.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        now = datetime.now(ZoneInfo(gv.TIME_ZONE))
        with rx.session() as session:
            stmt = select(func.count()).where(
                LecturerRegistrationToken.token == token,
                LecturerRegistrationToken.expires_at > now,
            )
            result = session.exec(stmt).one()
            return result == 1
