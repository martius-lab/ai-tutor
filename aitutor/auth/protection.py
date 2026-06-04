"""
Utilities for access control and role-based protection.
"""

import functools
from typing import Optional

import reflex as rx
from reflex_local_auth.login import LoginState
from sqlmodel import select

from aitutor.auth.state import SessionState
from aitutor.models import GlobalPermission, LectureRole, LinkUserLecture, UserRole


class LectureAccessState(SessionState):
    """State for route-based lecture access checks used by page protection."""

    @rx.var(initial_value=False)
    def is_lecture_member_or_admin(self) -> bool:
        """Whether the current user may access pages for members of this lecture."""
        return self._has_lecture_role_at_least(LectureRole.STUDENT)

    @rx.var(initial_value=False)
    def is_lecture_tutor_or_owner_or_admin(self) -> bool:
        """Whether the current user may access tutor/owner pages of this lecture."""
        return self._has_lecture_role_at_least(LectureRole.TUTOR)

    @rx.var(initial_value=False)
    def is_lecture_owner_or_admin(self) -> bool:
        """Whether the current user may access owner-only pages of this lecture."""
        return self._has_lecture_role_at_least(LectureRole.OWNER)

    def _has_lecture_role_at_least(self, required_role: LectureRole) -> bool:
        """Check the current route lecture role against the required lecture role."""
        if GlobalPermission.ADMIN in self.global_permissions:
            return True
        if self.authenticated_user is None or self.authenticated_user.id is None:
            return False

        try:
            lecture_id = int(self.lecture_id)
        except ValueError:
            return False

        with rx.session() as session:
            link = session.exec(
                select(LinkUserLecture).where(
                    LinkUserLecture.lecture_id == lecture_id,
                    LinkUserLecture.user_id == self.authenticated_user.id,
                )
            ).one_or_none()

        return link is not None and link.role >= required_role


def lecture_has_role_at_least(role) -> rx.vars.Var[bool]:
    """Check if the user has the specified role.

    Result is also positive if the user doesn't have the specified role but the global
    ADMIN permission.
    """
    return (
        SessionState.user_role is not None and SessionState.user_role >= role
    ) | SessionState.global_permissions.contains(GlobalPermission.ADMIN)


def has_permission(
    permission: GlobalPermission,
) -> rx.vars.Var[bool]:
    """Check if the user has the specified global permission."""
    okay = SessionState.global_permissions.contains(GlobalPermission.ADMIN)
    okay |= SessionState.global_permissions.contains(permission)
    return okay


def page_require_role_or_permission(
    *,
    required_role: Optional[UserRole] = None,
    allowed_permissions: Optional[list[GlobalPermission]] = None,
):
    """
    Protects a page. Allows access if the user has the required UserRole
    OR at least one of the allowed GlobalPermissions (ADMIN is always allowed).
    """
    # copy the list to avoid modifying the original and ensure ADMIN is always included
    perms_to_check = list(allowed_permissions) if allowed_permissions else []
    if GlobalPermission.ADMIN not in perms_to_check:
        perms_to_check.append(GlobalPermission.ADMIN)

    def decorator(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
        def protected_page():
            # Lecture role condition
            if required_role is not None:
                role_cond = rx.cond(
                    SessionState.user_role,
                    SessionState.user_role >= required_role,  # type: ignore
                    False,
                )
            else:
                role_cond = False

            # Global permissions condition
            if perms_to_check:
                perm_cond = SessionState.global_permissions.contains(perms_to_check[0])
                for perm in perms_to_check[1:]:
                    perm_cond = perm_cond | SessionState.global_permissions.contains(
                        perm
                    )
            else:
                perm_cond = False

            # grant access if the user has a required lecture role or global permission
            final_access_cond = role_cond | perm_cond

            return rx.fragment(
                rx.cond(
                    LoginState.is_hydrated & LoginState.is_authenticated,
                    rx.cond(
                        final_access_cond,
                        page(),
                        rx.center(
                            rx.text(
                                "You don't have the rights to access this page.",
                                size="6",
                            ),
                            height="85vh",
                        ),
                    ),
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Loading...", size="5"),
                            align="center",
                            justify="center",
                            on_mount=LoginState.redir,
                        ),
                        height="85vh",
                        width="100%",
                    ),
                )
            )

        protected_page.__name__ = page.__name__
        return protected_page

    return decorator


def page_require_lecture_role(
    required_role: LectureRole,
    allowed_permissions: Optional[list[GlobalPermission]] = None,
):
    """Protect a lecture route by lecture role or global permissions."""
    perms_to_check = list(allowed_permissions) if allowed_permissions else []
    if GlobalPermission.ADMIN not in perms_to_check:
        perms_to_check.append(GlobalPermission.ADMIN)

    def decorator(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
        def protected_page():
            match required_role:
                case LectureRole.OWNER:
                    lecture_access_cond = LectureAccessState.is_lecture_owner_or_admin
                case LectureRole.TUTOR:
                    lecture_access_cond = (
                        LectureAccessState.is_lecture_tutor_or_owner_or_admin
                    )
                case _:
                    lecture_access_cond = LectureAccessState.is_lecture_member_or_admin

            if perms_to_check:
                perm_cond = SessionState.global_permissions.contains(perms_to_check[0])
                for perm in perms_to_check[1:]:
                    perm_cond = perm_cond | SessionState.global_permissions.contains(
                        perm
                    )
            else:
                perm_cond = False

            final_access_cond = lecture_access_cond | perm_cond

            return rx.fragment(
                rx.cond(
                    LoginState.is_hydrated & LoginState.is_authenticated,
                    rx.cond(
                        final_access_cond,
                        page(),
                        rx.center(
                            rx.text(
                                "You don't have the rights to access this page.",
                                size="6",
                            ),
                            height="85vh",
                        ),
                    ),
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Loading...", size="5"),
                            align="center",
                            justify="center",
                            on_mount=LoginState.redir,
                        ),
                        height="85vh",
                        width="100%",
                    ),
                )
            )

        protected_page.__name__ = page.__name__
        return protected_page

    return decorator


def state_require_role_or_permission(
    *,
    required_role: Optional[UserRole] = None,
    allowed_permissions: Optional[list[GlobalPermission]] = None,
):
    """
    Protects a state event. Allows execution if the user has the required UserRole
    OR at least one of the allowed GlobalPermissions (ADMIN is always allowed).
    """
    # copy the list to avoid modifying the original and ensure ADMIN is always included
    perms_to_check = list(allowed_permissions) if allowed_permissions else []
    if GlobalPermission.ADMIN not in perms_to_check:
        perms_to_check.append(GlobalPermission.ADMIN)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self: SessionState, *args, **kwargs):
            if not self.is_authenticated:
                return

            # Lecture role condition
            has_role = False
            if required_role is not None and self.user_role is not None:
                has_role = self.user_role >= required_role

            # Global permissions condition
            has_perm = False
            if perms_to_check:
                has_perm = any(
                    perm in self.global_permissions for perm in perms_to_check
                )

            # grant access if the user has a required lecture role or global permission
            if has_role or has_perm:
                return func(self, *args, **kwargs)

        return wrapper

    return decorator
