"""State for the login and for the registration page."""

import asyncio
import email.utils
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
import reflex_local_auth
from reflex_local_auth.user import LocalUser
from sqlmodel import func, select

import aitutor.global_vars as GV
from aitutor.account_emails import send_signup_welcome_email
from aitutor.config import get_config
from aitutor.language_state import language_from_value
from aitutor.models import (
    GlobalPermission,
    LecturerRegistrationToken,
    Permission,
    UserInfo,
    UserRole,
)

logger = logging.getLogger(__name__)

AUTH_FIELD_MAX_LENGTHS: dict[str, int] = {
    "username": GV.USERNAME_MAX_LEN,
    "email": GV.EMAIL_MAX_LEN,
    "password": GV.PASSWORD_MAX_LEN,
    "confirm_password": GV.PASSWORD_MAX_LEN,
    "registration_code": GV.REGISTRATION_CODE_MAX_LEN,
}


class MyLoginState(reflex_local_auth.LoginState):
    """
    A custom login state class that handles user login.
    """

    @rx.event
    def on_load(self):
        """function that gets called when the login page loads"""
        self.error_message = ""


class MyRegisterState(reflex_local_auth.RegistrationState):
    """
    A custom registration state class that handles user registration.
    """

    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    registration_code: str = ""
    welcome_email_sent: bool = False
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
        self.password = value[: AUTH_FIELD_MAX_LENGTHS["password"]]

    @rx.event
    def set_confirm_password(self, value: str):
        """Set the confirm password."""
        self.confirm_password = value[: AUTH_FIELD_MAX_LENGTHS["confirm_password"]]

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
        self.welcome_email_sent = False
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
        self.welcome_email_sent = False
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

                session.commit()
                session.refresh(user_info)

                local_user = session.get(LocalUser, self.new_user_id)
                username = local_user.username if local_user else None

            welcome_email_sent = False
            welcome_email_failed = False
            try:
                if username:
                    await asyncio.to_thread(
                        send_signup_welcome_email,
                        to_email=user_info.email,
                        username=username,
                        language=user_info.language,
                    )
                    welcome_email_sent = True
            except Exception:
                logger.exception(
                    "Failed to send signup welcome email for user_id=%s.",
                    self.new_user_id,
                )
                welcome_email_failed = True

            self.clear_state_vars()
            self.welcome_email_sent = welcome_email_sent
            self.welcome_email_failed = welcome_email_failed
            self.success = True
            self.error_message = ""
            if not welcome_email_failed:
                yield registration_result
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
        now = datetime.now(ZoneInfo(GV.TIME_ZONE))
        with rx.session() as session:
            stmt = select(func.count()).where(
                LecturerRegistrationToken.token == token,
                LecturerRegistrationToken.expires_at > now,
            )
            result = session.exec(stmt).one()
            return result == 1
