"""State for the login and for the registration page."""

import re

import reflex as rx
import reflex_local_auth

from aitutor.models import UserInfo, UserRole
from aitutor.config import get_config


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

    # This event handler must be named something besides `handle_registration`!!!
    @rx.event
    def handle_custom_registration(self, form_data):
        """
        Handles the registration process for a user using their email.

        Args:
            form_data (dict): A dictionary containing the user's registration data.

        Returns:
            Any: The result of the registration process.
        """
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

        registration_result = self.handle_registration(form_data)
        if self.new_user_id >= 0:
            self.clear_state_vars()
            with rx.session() as session:
                session.add(
                    UserInfo(
                        email=form_data["email"],
                        role=UserRole.STUDENT,
                        user_id=self.new_user_id,
                    )
                )
                session.commit()
        return registration_result
