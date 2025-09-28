"""
The state and event handlers for user registration,
including integration with local authentication and user role management.
"""

import reflex as rx
import reflex_local_auth
import sqlmodel
from aitutor.models import UserInfo, UserRole, Language
from typing import Optional

import aitutor.routes as routes
from aitutor import pages


class SessionState(reflex_local_auth.LocalAuthState):
    """
    The state for managing user sessions.
    """

    language: Language = Language.EN

    @rx.event
    def global_load(self):
        """
        Load the relevant session information.
        This method should be called in all pages' on_load methods.
        """
        with rx.session() as session:
            # set the language based on the authenticated user's language
            user_info = session.exec(
                UserInfo.select().where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info:
                self.language = user_info.language

    @rx.event
    def toggle_language(self):
        """Toggle the language between English and German."""
        with rx.session() as session:
            user_info = session.exec(
                UserInfo.select().where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            match self.language:
                case Language.EN:
                    self.language = Language.DE
                case _:
                    self.language = Language.EN
            if user_info:
                user_info.language = self.language
                session.add(user_info)
                session.commit()

    @rx.var(cache=True, initial_value=None)
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

    async def perform_logout(self):
        """
        Handles the logout process for the authenticated user.
        """
        states = [
            pages.ChatState,
            pages.HomeState,
            pages.ExercisesState,
            pages.FinishedViewState,
            pages.FinishedViewTeacherState,
            pages.ManageExercisesState,
            pages.SubmissionsState,
        ]
        for state in states:
            # get the state
            state_instance = await self.get_state(state)
            # clear the state
            state_instance.on_logout()

        # logout
        self.do_logout()
        return rx.redirect(routes.HOME, replace=True)

    @rx.var(cache=True, initial_value=None)
    def user_role(self) -> UserRole | None:
        """
        Retrieves the role of the authenticated user.

        Returns:
            UserRole: The role of the authenticated user.
        """
        if self.authenticated_user_info is None:
            return None
        return self.authenticated_user_info.role

    @rx.var(cache=True, initial_value=None)
    def user_id(self) -> int | None:
        """
        Retrieves the ID of the authenticated user.

        Returns:
            int: The ID of the authenticated user.
        """
        if self.authenticated_user_info is None:
            return None
        return self.authenticated_user_info.user_id


class MyRegisterState(reflex_local_auth.RegistrationState):
    """
    A custom registration state class that handles user registration
    and integrates with local authentication and user role management.
    """

    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""

    @rx.event
    def on_load(self):
        """function that gets called when the register page loads"""
        self.clear_state_vars()
        self.error_message = ""
        self.success = False

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

    def clear_state_vars(self):
        """Clear the state variables."""
        self.username = ""
        self.email = ""
        self.password = ""
        self.confirm_password = ""

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


class MyLoginState(reflex_local_auth.LoginState):
    """
    A custom login state class that handles user login
    and integrates with local authentication and user role management.
    """

    @rx.event
    def on_load(self):
        """function that gets called when the login page loads"""
        self.error_message = ""
