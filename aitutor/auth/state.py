"""
The state and event handlers for user registration,
including integration with local authentication and user role management.
"""

import reflex as rx
import reflex_local_auth
import sqlmodel
from aitutor.models import UserInfo, UserRole, LanguageEnum
from typing import Optional

import aitutor.routes as routes
from aitutor import pages


class SessionState(reflex_local_auth.LocalAuthState):
    """
    The state for managing user sessions.
    """

    language: LanguageEnum = LanguageEnum.EN

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
                case LanguageEnum.EN:
                    self.language = LanguageEnum.DE
                    if user_info:
                        user_info.language = LanguageEnum.DE
                        session.add(user_info)
                        session.commit()
                case LanguageEnum.DE:
                    self.language = LanguageEnum.EN
                    if user_info:
                        user_info.language = LanguageEnum.EN
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
