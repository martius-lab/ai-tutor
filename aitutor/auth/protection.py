"""
Utilities for access control and role-based protection.
"""

import functools
from typing import Optional

import reflex as rx
from reflex_local_auth.login import LoginState

from aitutor.auth.state import SessionState
from aitutor.models import GlobalRole, UserRole

# LECTURE SPECIFIC ROLES ---------------------------------------------------------------


def lecture_has_role_at_least(role):
    """
    Check if the user has the required role to access a specific feature.
    """
    user_role = SessionState.user_role
    return (
        (user_role is not None and user_role >= role)
        | SessionState.global_permissions.contains(GlobalRole.ADMIN)
        | SessionState.global_permissions.contains(GlobalRole.MAINTAINER)
    )


def lecture_state_require_role_at_least(required_role):
    """
    Checks if the user is authenticated and has the required role (in the backend).
    This decorator should be called with the on_load method of a state class.
    It will prevent that data is loaded if the user does not have the required role.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self: SessionState, *args, **kwargs):
            if self.is_authenticated and self.user_role >= required_role:
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


# CHECK FOR GLOBAL ROLES OR LECTURE ROLES ----------------------------------------------


def page_require_role_or_permission(
    *,
    required_role: Optional[UserRole] = None,
    allowed_permissions: Optional[list[GlobalRole]] = None,
):
    """
    Protects a page. Allows access if the user has the required UserRole
    OR at least one of the allowed GlobalRoles (ADMIN is always allowed).
    """
    # copy the list to avoid modifying the original and ensure ADMIN is always included
    perms_to_check = list(allowed_permissions) if allowed_permissions else []
    if GlobalRole.ADMIN not in perms_to_check:
        perms_to_check.append(GlobalRole.ADMIN)

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


def state_require_role_or_permission(
    *,
    required_role: Optional[UserRole] = None,
    allowed_permissions: Optional[list[GlobalRole]] = None,
):
    """
    Protects a state event. Allows execution if the user has the required UserRole
    OR at least one of the allowed GlobalRoles (ADMIN is always allowed).
    """
    # copy the list to avoid modifying the original and ensure ADMIN is always included
    perms_to_check = list(allowed_permissions) if allowed_permissions else []
    if GlobalRole.ADMIN not in perms_to_check:
        perms_to_check.append(GlobalRole.ADMIN)

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
