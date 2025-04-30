"""
The state and event handlers for user registration,
including integration with local authentication and user role management.
"""

import reflex as rx
import reflex_local_auth

from aitutor.auth.models import UserInfo, UserRole

from typing import Optional

import sqlmodel


class SessionState(reflex_local_auth.LocalAuthState):
    """
    A custom local authentication state class that provides additional
    functionality for retrieving authenticated user information.
    """

    @rx.var(cache=True)
    def authenticated_user_info(self) -> Optional[UserInfo]:
        """
        Retrieves information about the currently authenticated user.

        Returns:
            Optional[UserInfo]: The authenticated user's information,
            or None if not found.
        """
        if (
            self.authenticated_user is None
            or self.authenticated_user.id is None
            or self.authenticated_user.id < 0
        ):
            return None
        with rx.session() as session:
            return session.exec(
                sqlmodel.select(UserInfo).where(
                    UserInfo.user_id == self.authenticated_user.id
                ),
            ).one_or_none()

    def on_load(self):
        """
        Handles the loading of the session state.
        """
        if not self.is_authenticated:
            return reflex_local_auth.LoginState.redir()

    def perform_logout(self):
        """
        Handles the logout process for the authenticated user.
        """
        self.do_logout()
        return rx.redirect("/")

    @rx.var()
    def user_role(self) -> UserRole | None:
        """
        Retrieves the role of the authenticated user.

        Returns:
            UserRole: The role of the authenticated user.
        """
        if self.authenticated_user_info is None:
            return None
        return self.authenticated_user_info.role


class MyRegisterState(reflex_local_auth.RegistrationState):
    """
    A custom registration state class that handles user registration
    and integrates with local authentication and user role management.
    """

    # This event handler must be named something besides `handle_registration`!!!
    def handle_registration_email(self, form_data):
        """
        Handles the registration process for a user using their email.

        Args:
            form_data (dict): A dictionary containing the user's registration data.

        Returns:
            Any: The result of the registration process.
        """
        registration_result = self.handle_registration(form_data)
        if self.new_user_id >= 0:
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
