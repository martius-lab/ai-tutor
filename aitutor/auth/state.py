"""
The state for managing user sessions.
"""

from typing import Callable, Optional

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
            pages.AllLecturesState,
            pages.ChatState,
            pages.EditLectureState,
            pages.HomeState,
            pages.ExercisesState,
            pages.FinishedViewState,
            pages.FinishedViewTutorState,
            pages.LectureExercisesState,
            pages.LectureManageExercisesState,
            pages.LectureManagePromptsState,
            pages.LectureManageTagsState,
            pages.LectureMembersState,
            pages.LectureOverviewState,
            pages.LectureReportsState,
            pages.LectureReportViewState,
            pages.LectureSubmissionsState,
            pages.LectureTokenAnalyzerState,
            pages.ManageConfigState,
            pages.ManageExercisesState,
            pages.ManageTagsState,
            pages.ManagePromptsState,
            pages.ManageUsersState,
            pages.MyLecturesState,
            pages.ReportsState,
            pages.ReportViewState,
            pages.SubmissionsState,
            pages.TokenAnalyzerState,
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

    @rx.var(cache=True, initial_value=False)
    def is_global_admin(self) -> bool:
        """Whether the current user has global ADMIN permission."""
        return GlobalPermission.ADMIN in self.global_permissions

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
            return permissions  # type: ignore

    def has_permission(self, permission: GlobalPermission) -> bool:
        """Return whether the current user has a global permission.

        Global ADMIN permission grants all global permissions.
        """
        return (
            permission in self.global_permissions
            or GlobalPermission.ADMIN in self.global_permissions
        )

    def _get_router_params(self) -> dict[str, str]:
        # Wrap this in a method so we only directly access self.router.page in one
        # place.  RouterData.page is deprecated and thus triggers a deprecation warning.
        # However, the suggestion to use RouterData.url instead is not helpful, as it
        # does not (yet?) provide access to the route parameters.
        return self.router.page.params

    def get_route_param_or_default[T](
        self, param_name: str, default: T, dtype: Callable[..., T] = str
    ) -> T:
        """Get a route parameter or return a default value if not present.

        Args:
            param_name: The name of the route parameter to retrieve.
            default_value: The value to return if the parameter is not present.
            output_type: The type to which the parameter value should be cast.
        """
        if param_name in self._get_router_params():
            return dtype(self._get_router_params()[param_name])
        else:
            return default

    def get_route_param_or_error[T](
        self, param_name: str, dtype: Callable[..., T] = str
    ) -> T:
        """Get a route parameter or raise an error if not present.

        Args:
            param_name: The name of the route parameter to retrieve.
            output_type: The type to which the parameter value should be cast.

        Raises:
            KeyError: If the parameter is not provided in the route.
        """
        if param_name not in self._get_router_params():
            raise KeyError(f"Route parameter '{param_name}' not found.")
        return dtype(self._get_router_params()[param_name])
