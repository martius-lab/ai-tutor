"""State for the login and for the registration page."""

import asyncio
import logging
import re

import reflex as rx
import reflex_local_auth
from reflex_local_auth.user import LocalUser

from aitutor.account_emails import send_signup_welcome_email
from aitutor.config import get_config
from aitutor.language_state import language_from_value
from aitutor.mail import EmailConfigurationError, EmailDeliveryError
from aitutor.models import UserInfo, UserRole

logger = logging.getLogger(__name__)


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

    @rx.event
    def set_username(self, value: str):
        """Set the username."""
        self.username = value

    @rx.event
    def set_email(self, value: str):
        """Set the email."""
        self.email = value

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
        self.registration_code = value

    @rx.event
    def on_load(self):
        """function that gets called when the register page loads"""
        self.clear_state_vars()
        self.error_message = ""
        self.success = False

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
            language = language_from_value(form_data.get("language"))
            # check for allowed user name
            if not re.match(r"^[a-zA-Z0-9._-]+$", form_data["username"]):
                self.error_message = (
                    "Username can only contain letters, numbers and '. _ -'"
                )
                self.username = ""
                return

            # check for the correct registration code
            registration_code = get_config().registration_code
            if form_data["registration_code"] != registration_code:
                self.error_message = "The registration code is wrong."
                self.registration_code = ""
                return

            validation_errors = self._validate_fields(
                form_data["username"],
                form_data["password"],
                form_data["confirm_password"],
            )
            if validation_errors:
                self.new_user_id = -1
                yield validation_errors
                return

            self._register_user(form_data["username"], form_data["password"])
            if self.new_user_id < 0:
                return

            welcome_email_sent = False
            welcome_email_failed = False
            with rx.session() as session:
                user_info = UserInfo(
                    email=form_data["email"],
                    role=UserRole.STUDENT,
                    user_id=self.new_user_id,
                    language=language,
                )
                session.add(user_info)
                session.commit()
                try:
                    local_user = session.get(LocalUser, self.new_user_id)
                    if local_user is not None:
                        await asyncio.to_thread(
                            send_signup_welcome_email,
                            to_email=user_info.email,
                            username=local_user.username,
                            language=user_info.language,
                        )
                        welcome_email_sent = True
                except (EmailConfigurationError, EmailDeliveryError):
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
                yield type(self).successful_registration
        finally:
            self.registration_in_progress = False
