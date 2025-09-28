"""State for the login and for the registration page."""

import reflex as rx
import reflex_local_auth

from aitutor.models import UserInfo, UserRole


class ShowPasswordMixin(rx.State, mixin=True):
    """Mixin to add show password functionality to the login and register page."""

    password_visible: bool = False

    @rx.event
    def toggle_password_visibility(self):
        """Toggle the visibility of the password."""
        self.password_visible = not self.password_visible


class MyLoginState(ShowPasswordMixin, reflex_local_auth.LoginState):
    """
    A custom login state class that handles user login.
    """

    # overrides the variable in the ShowPasswordMixin
    password_visible: bool = False

    @rx.event
    def on_load(self):
        """function that gets called when the login page loads"""
        self.error_message = ""
        self.password_visible = False


class MyRegisterState(ShowPasswordMixin, reflex_local_auth.RegistrationState):
    """
    A custom registration state class that handles user registration.
    """

    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""

    # overrides the variable in the ShowPasswordMixin
    password_visible: bool = False

    @rx.event
    def on_load(self):
        """function that gets called when the register page loads"""
        self.clear_state_vars()
        self.error_message = ""
        self.success = False
        self.password_visible = False

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

    def clear_state_vars(self):
        """Clear the state variables."""
        self.username = ""
        self.email = ""
        self.password = ""
        self.confirm_password = ""
