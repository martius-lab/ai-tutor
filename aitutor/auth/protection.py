"""
Utilities for access control and role-based protection.
"""

import functools

import reflex as rx
from reflex_local_auth.login import LoginState

from aitutor.auth.state import SessionState
from aitutor.models import UserRole


def lecture_has_role_at_least(role):
    """
    Check if the user has the required role to access a specific feature.
    """
    user_role = SessionState.user_role
    return user_role is not None and user_role >= role


def lecture_page_require_role_at_least(required_role: UserRole):
    """
    Checks if the user is authenticated and has the required role (in the frontend).
    This decorator should be called with the page function.
    It prevents that the page is rendered if the user does not have the required role.
    """

    def decorator(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
        def protected_page():
            userrole = SessionState.user_role
            return rx.fragment(
                rx.cond(
                    LoginState.is_hydrated & LoginState.is_authenticated,
                    rx.cond(
                        rx.cond(userrole, userrole >= required_role, False),  # type: ignore
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
