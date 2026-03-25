"""
The state for managing user sessions.
"""

from typing import Optional

import reflex as rx
import reflex_local_auth
from sqlmodel import select

import aitutor.routes as routes
from aitutor import pages
from aitutor.models import GlobalPermission, Language, Permission, UserInfo, UserRole


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
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info:
                self.language = user_info.language

    @rx.event
    def toggle_language(self):
        """Toggle the language between English and German."""
        with rx.session() as session:
            user_info = session.exec(
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
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
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id),
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
            pages.FinishedViewTutorState,
            pages.ManageExercisesState,
            pages.ManageTagsState,
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

    @rx.var(cache=True, initial_value=[])
    def global_permissions(self) -> list[GlobalPermission]:
        """
        Retrieves a list of global permissions (Enums) for the authenticated user.
        """
        if (
            self.authenticated_user is None
            or self.authenticated_user.id is None
            or self.authenticated_user.id < 0
        ):
            return []
        with rx.session() as session:
            permissions = session.exec(
                select(Permission.permission).where(
                    Permission.user_id == self.authenticated_user.id
                )
            ).all()
            return permissions # type: ignore
