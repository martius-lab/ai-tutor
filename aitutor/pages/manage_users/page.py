"""Admin-page to manage user accounts."""

import reflex as rx

from aitutor import routes
from aitutor.auth.protection import page_require_role_or_permission
from aitutor.models import GlobalPermission, UserRole
from aitutor.pages.manage_users.components import edit_user_dialog, users_table
from aitutor.pages.navbar import with_navbar
from aitutor.pages.navbar_admin import with_admin_navbar


@with_navbar(routes.ADMIN_SETTINGS)
@with_admin_navbar(routes.MANAGE_USERS)
@page_require_role_or_permission(
    required_role=UserRole.ADMIN,
    allowed_permissions=[GlobalPermission.ADMIN, GlobalPermission.MAINTAINER],
)
def manage_users_page() -> rx.Component:
    """Manage users page."""
    return rx.center(
        rx.vstack(
            users_table(),
            edit_user_dialog(),
            spacing="3",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="100%",
    )
