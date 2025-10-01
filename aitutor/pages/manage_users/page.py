"""Admin-page to manage user accounts."""

import reflex as rx


from aitutor import routes
from aitutor.models import LocalUser, UserInfo, UserRole
from aitutor.pages.manage_users.state import ManageUsersState
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import page_require_role_at_least


def role_to_text(role: UserRole):
    """Convert a UserRole to string in a way that works for reflex."""
    return rx.cond(
        role == UserRole.ADMIN,
        UserRole.ADMIN.name,
        rx.cond(
            role == UserRole.TEACHER,
            UserRole.TEACHER.name,
            rx.cond(role == UserRole.STUDENT, UserRole.STUDENT.name, "Unknown"),
        ),
    )


def user_table_row(user: tuple[LocalUser, UserInfo]) -> rx.Component:
    """Create a single row of the users table."""
    return rx.table.row(
        rx.table.cell(user[0].id),
        rx.table.cell(user[0].username),
        rx.table.cell(user[1].email),
        rx.table.cell(role_to_text(user[1].role)),
        rx.table.cell(
            rx.cond(
                user[0].enabled,
                rx.icon("square-check"),
                rx.icon("square-x", color="red"),
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Edit",
                    color_scheme="blue",
                    on_click=ManageUsersState.open_edit_dialog(user[0].id),
                ),
                rx.button(
                    "Delete",
                    color_scheme="red",
                    disabled=True,  # TODO implement delete user functionality
                ),
                spacing="2",
            ),
        ),
    )


def form_label(text: str) -> rx.Component:
    """Create a form label."""
    return rx.text(
        text,
        size="3",
        weight="medium",
        text_align="left",
        width="100%",
        padding_top="1.5em",
        padding_bottom="0.5em",
    )


def edit_user_dialog() -> rx.Component:
    """Dialog for editing users."""
    return rx.cond(
        ManageUsersState.edited_user != None,  # noqa: E711
        rx.dialog.root(
            rx.dialog.content(
                rx.hstack(
                    rx.badge(
                        rx.icon(tag="wrench", size=34),
                        color_scheme="orange",
                        radius="full",
                    ),
                    rx.vstack(
                        rx.dialog.title(
                            "Edit User",
                            weight="bold",
                            margin="0",
                        ),
                        rx.dialog.description(
                            "Really what should be written here?",
                        ),
                        spacing="1",
                        height="100%",
                        align_items="start",
                        justify_content="start",
                    ),
                    height="100%",
                    spacing="4",
                    margin_bottom="1.5em",
                    align_items="start",
                    width="100%",
                ),
                rx.form(
                    (
                        form_label("Username"),
                        rx.input(
                            default_value=ManageUsersState.edited_user[0].username,
                            size="3",
                            width="100%",
                            type="text",
                            name="username",
                        ),
                        form_label("Email"),
                        rx.input(
                            default_value=ManageUsersState.edited_user[1].email,
                            size="3",
                            width="100%",
                            type="text",
                            name="email",
                        ),
                        form_label("New password"),
                        rx.input(
                            placeholder="Leave empty to keep current password",
                            size="3",
                            width="100%",
                            type="password",
                            name="new_password",
                        ),
                        form_label("Role"),
                        rx.select(
                            (
                                UserRole.ADMIN.name,
                                UserRole.TEACHER.name,
                                UserRole.STUDENT.name,
                            ),
                            default_value=role_to_text(
                                ManageUsersState.edited_user[1].role
                            ),
                            size="3",
                            width="100%",
                            name="role",
                        ),
                        form_label("Enabled"),
                        rx.checkbox(
                            name="enabled",
                            default_checked=ManageUsersState.edited_user[0].enabled,
                        ),
                        # buttons
                        rx.hstack(
                            rx.button(
                                "Cancel",
                                color_scheme="gray",
                                type="button",
                                on_click=ManageUsersState.close_edit_dialog(),
                            ),
                            rx.button(
                                "Save",
                                color_scheme="blue",
                                type="submit",
                            ),
                            spacing="2",
                            margin_top="1.5em",
                            justify="end",
                            width="100%",
                        ),
                    ),
                    on_submit=ManageUsersState.update_user,
                ),
            ),
            open=ManageUsersState.edit_dialog_is_open,
        ),
    )


def users_table() -> rx.Component:
    """Component to display the users table."""
    return rx.fragment(
        # head cells for the main table
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    # TODO language
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Username"),
                    rx.table.column_header_cell("Email"),
                    rx.table.column_header_cell("Role"),
                    rx.table.column_header_cell("Enabled"),
                    rx.table.column_header_cell("Action"),
                ),
            ),
            # dynamically render each new entry
            rx.table.body(rx.foreach(ManageUsersState.users, user_table_row)),
            variant="surface",
            size="3",
            width="85vw",
            overflow_y="auto",
            max_height="66vh",
        ),
    )


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
