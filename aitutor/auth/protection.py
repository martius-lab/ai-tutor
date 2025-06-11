"""
Utilities for access control and role-based protection.
"""

import reflex as rx
from reflex_local_auth.login import LoginState
from aitutor.auth.state import SessionState
from aitutor.models import UserRole


def has_role_at_least(role):
    """
    Check if the user has the required role to access a specific feature.
    """
    user_role = SessionState.user_role
    return user_role is not None and user_role >= role


def require_role_at_least(role: UserRole):
    """
    Decorator to restrict access to a page based on the user's role.

    Parameters
    ----------
    role : UserRole
        The minimum role required to access the page.

    Returns
    -------
    Callable
        A decorated page component callable that enforces the role restriction.
    """

    def decorator(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
        def protected_page():
            userrole = SessionState.user_role  # type: ignore
            return rx.fragment(
                rx.cond(
                    LoginState.is_hydrated & LoginState.is_authenticated,  # type: ignore
                    rx.cond(
                        rx.cond(userrole, userrole >= role, False),  # type: ignore
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
                        # When this text mounts, it will redirect to the login page
                        rx.text("Loading...", size="6", on_mount=LoginState.redir),
                        height="85vh",
                    ),
                )
            )

        protected_page.__name__ = page.__name__
        return protected_page

    return decorator
