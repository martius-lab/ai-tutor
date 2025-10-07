"""Admin-page to manage user accounts."""

import reflex as rx


from aitutor import routes
from aitutor.models import UserRole
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least
from aitutor.pages.manage_users.components import users_table, edit_user_dialog


@with_navbar(routes.MANAGE_USERS)
@page_require_role_at_least(UserRole.ADMIN)
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
        width="90%",
    )
