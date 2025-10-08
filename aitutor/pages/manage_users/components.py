"""Components for the manage users page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.models import LocalUser, UserInfo, UserRole
from aitutor.pages.manage_users.state import ManageUsersState
from aitutor.pages.login_and_registration.components import password_input


def role_to_text(role: UserRole):
    """Convert a UserRole to string in a way that works for reflex."""
    return rx.match(
        role,
        (UserRole.ADMIN, UserRole.ADMIN.name),
        (UserRole.TUTOR, UserRole.TUTOR.name),
        (UserRole.STUDENT, UserRole.STUDENT.name),
        "Unknown",
    )


def delete_user_button(user: LocalUser) -> rx.Component:
    """Button to delete a user with a confirmation dialog."""
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                rx.flex(
                    rx.icon("trash", size=15), LS.delete, gap="0.5em", align="center"
                ),
                color_scheme="red",
                _hover={"cursor": "pointer"},
            ),
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title(LS.delete_user + f" '{user.username}'"),
            rx.alert_dialog.description(LS.delete_user_description),
            rx.hstack(
                rx.spacer(),
                rx.alert_dialog.cancel(
                    rx.button(
                        rx.text(LS.cancel),
                        _hover={"cursor": "pointer"},
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.alert_dialog.action(
                    rx.button(
                        LS.delete,
                        color_scheme="red",
                        on_click=ManageUsersState.delete_user(user.id),  # type: ignore
                        _hover={"cursor": "pointer"},
                    ),
                ),
                margin_top="1em",
            ),
        ),
    )


def user_table_row(user: tuple[LocalUser, UserInfo]) -> rx.Component:
    """Create a single row of the users table."""
    return rx.table.row(
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
                    rx.flex(
                        rx.icon("pen", size=15), LS.edit, gap="0.5em", align="center"
                    ),
                    color_scheme="blue",
                    on_click=ManageUsersState.open_edit_dialog(user[0].id),  # type: ignore
                    _hover={"cursor": "pointer"},
                ),
                delete_user_button(user[0]),
                spacing="2",
            ),
        ),
    )


def form_label(text: str | rx.vars.StringVar[str]) -> rx.Component:
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

    def _helper(local_user: LocalUser, user_info: UserInfo) -> rx.Component:
        return rx.dialog.root(
            rx.dialog.content(
                rx.hstack(
                    rx.badge(
                        rx.icon(tag="pen", size=34),
                        color_scheme="orange",
                        radius="full",
                    ),
                    rx.dialog.title(
                        LS.edit_user,
                        weight="bold",
                        margin="0",
                    ),
                    height="100%",
                    spacing="4",
                    margin_bottom="1.5em",
                    align="center",
                    width="100%",
                ),
                rx.form(
                    (
                        form_label(LS.username),
                        rx.input(
                            default_value=local_user.username,
                            size="3",
                            width="100%",
                            type="text",
                            name="username",
                        ),
                        form_label(LS.email),
                        rx.input(
                            default_value=user_info.email,
                            size="3",
                            width="100%",
                            type="text",
                            name="email",
                        ),
                        form_label(LS.new_password),
                        password_input(
                            name="new_password",
                            size="3",
                            placeholder=LS.new_password_placeholder,
                            state=ManageUsersState,
                        ),
                        form_label(LS.role),
                        rx.hstack(
                            rx.select(
                                (
                                    UserRole.ADMIN.name,
                                    UserRole.TUTOR.name,
                                    UserRole.STUDENT.name,
                                ),
                                default_value=role_to_text(user_info.role),  # type: ignore
                                size="3",
                                name="role",
                            ),
                            rx.dialog.root(
                                rx.dialog.trigger(
                                    rx.icon("info"), _hover={"cursor": "pointer"}
                                ),
                                rx.dialog.content(rx.markdown(LS.roles_description)),
                            ),
                            align="center",
                        ),
                        form_label(LS.enabled),
                        rx.checkbox(
                            name="enabled",
                            default_checked=local_user.enabled,
                        ),
                        # buttons
                        rx.hstack(
                            rx.button(
                                LS.cancel,
                                color_scheme="gray",
                                type="button",
                                on_click=ManageUsersState.close_edit_dialog(),
                                _hover={"cursor": "pointer"},
                            ),
                            rx.button(
                                LS.save,
                                color_scheme="blue",
                                type="submit",
                                _hover={"cursor": "pointer"},
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
        )

    return rx.cond(
        ManageUsersState.edited_user != None,  # noqa: E711
        _helper(
            local_user=ManageUsersState.edited_user[0],  # type: ignore
            user_info=ManageUsersState.edited_user[1],  # type: ignore
        ),
    )


def users_table() -> rx.Component:
    """Component to display the users table."""
    return rx.fragment(
        # head cells for the main table
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(LS.username),
                    rx.table.column_header_cell(LS.email),
                    rx.table.column_header_cell(LS.role),
                    rx.table.column_header_cell(LS.enabled),
                    rx.table.column_header_cell(""),
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
