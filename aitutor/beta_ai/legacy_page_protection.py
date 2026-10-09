"""Preserve access rules for the original global Beta AI pages."""

import reflex as rx
from reflex_local_auth.login import LoginState

from aitutor.auth.state import SessionState
from aitutor.language_state import LanguageState
from aitutor.models import GlobalPermission, UserRole


def legacy_beta_page_require_role_or_permission(
    *,
    required_role: UserRole | None = None,
    allowed_permissions: list[GlobalPermission] | None = None,
):
    """
    Preserve the original global Beta AI page protection during integration.

    Only the pre-lecture Beta AI pages use this compatibility guard.
    Allows access if the user has the required UserRole
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
                                LanguageState.access_denied,
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
