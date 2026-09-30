"""Components for the manage users page."""

import reflex as rx

import aitutor.global_vars as gv
from aitutor.components import password_input
from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState as LS
from aitutor.models import LocalUser, UserInfo, UserRole
from aitutor.pages.manage_users.state import (
    MANAGE_USERS_FIELD_MAX_LENGTHS,
    ManageUsersState,
)


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

    return destructive_confirm(
        title=LS.delete_user + f" '{user.username}'",
        description=LS.delete_user_description,
        confirm_text=LS.delete,
        cancel_text=LS.cancel,
        on_confirm=ManageUsersState.delete_user(user.id),  # type: ignore
        trigger=rx.button(
            rx.flex(
                rx.icon("trash", size=15),
                LS.delete,
                gap="0.5em",
                align="center",
            ),
            color_scheme="red",
            _hover={"cursor": "pointer"},
        ),
    )


def last_login_text(user_info: UserInfo) -> rx.Component:
    """Show the time of the last login or a placeholder if there was none yet."""
    return rx.cond(
        user_info.last_login_at == None,
        rx.text(LS.never),
        rx.moment(user_info.last_login_at, format=gv.MOMENT_DATETIME_FORMAT),
    )


def verified_icon(user_info: UserInfo, pending_email: rx.Var[str]) -> rx.Component:
    """Show whether the email address of a user is confirmed."""
    return rx.cond(
        user_info.verified,
        rx.cond(
            pending_email != "",
            rx.hover_card.root(
                rx.hover_card.trigger(rx.icon("clock", color=rx.color("amber", 9))),
                rx.hover_card.content(
                    rx.text(LS.email_change_pending_tooltip, " ", pending_email)
                ),
            ),
            rx.icon("square-check"),
        ),
        # not an error but a pending state, so amber instead of red
        rx.icon("square-x", color=rx.color("amber", 9)),
    )


def user_table_row(user: tuple[LocalUser, UserInfo, str]) -> rx.Component:
    """
    Create a single row of the users table.

    The third element is the address of a pending email change, "" if there is none.
    """
    return rx.table.row(
        rx.table.cell(user[0].username),
        rx.table.cell(role_to_text(user[1].role)),
        rx.table.cell(
            rx.cond(
                user[0].enabled,
                rx.icon("square-check"),
                rx.icon("square-x", color=rx.color("red", 9)),
            )
        ),
        rx.table.cell(verified_icon(user[1], user[2])),  # type: ignore
        rx.table.cell(rx.moment(user[1].created_at, format=gv.MOMENT_DATETIME_FORMAT)),
        rx.table.cell(last_login_text(user[1])),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.flex(
                        rx.icon("pen", size=15), LS.edit, gap="0.5em", align="center"
                    ),
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


def email_verification_info(user_info: UserInfo) -> rx.Component:
    """
    Verification state of the email address of the edited user.

    Also offers to resend the confirmation link if there is anything to confirm.
    """
    has_pending_change = ManageUsersState.edited_user_pending_email != ""
    return rx.vstack(
        rx.hstack(
            rx.cond(
                user_info.verified,
                rx.cond(
                    has_pending_change,
                    rx.badge(LS.email_change_pending, color_scheme="amber"),
                    rx.badge(LS.email_verified, color_scheme="green"),
                ),
                rx.badge(LS.email_not_verified, color_scheme="amber"),
            ),
            rx.cond(
                ~user_info.verified | has_pending_change,
                rx.button(
                    rx.icon("mail", size=15),
                    LS.resend_verification_email,
                    size="1",
                    variant="soft",
                    # do not submit the form
                    type="button",
                    on_click=ManageUsersState.resend_verification_email_to_edited_user,
                    loading=ManageUsersState.resend_in_progress,
                    _hover={"cursor": "pointer"},
                ),
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            user_info.verified & has_pending_change,
            rx.text(
                LS.email_change_pending_description,
                " ",
                user_info.email,
                size="2",
                color_scheme="gray",
            ),
        ),
        spacing="2",
        padding_top="0.5em",
        width="100%",
    )


def edit_user_dialog() -> rx.Component:
    """Dialog for editing users."""

    def _helper(local_user: LocalUser, user_info: UserInfo) -> rx.Component:
        return rx.dialog.root(
            rx.dialog.content(
                rx.hstack(
                    rx.badge(
                        rx.icon(tag="pen", size=34),
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
                            max_length=MANAGE_USERS_FIELD_MAX_LENGTHS["username"],
                        ),
                        form_label(LS.email),
                        rx.input(
                            # show the address of a pending change, so that saving the
                            # form without touching this field keeps the change
                            default_value=rx.cond(
                                ManageUsersState.edited_user_pending_email != "",
                                ManageUsersState.edited_user_pending_email,
                                user_info.email,
                            ),
                            size="3",
                            width="100%",
                            type="text",
                            name="email",
                            max_length=MANAGE_USERS_FIELD_MAX_LENGTHS["email"],
                        ),
                        email_verification_info(user_info),
                        form_label(LS.new_password),
                        password_input(
                            name="new_password",
                            placeholder=LS.new_password_placeholder,
                            size="3",
                            width="100%",
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
                        form_label(LS.permissions),
                        rx.vstack(
                            rx.checkbox(
                                LS.admin_permission,
                                name="global_permission_admin",
                                default_checked=ManageUsersState.edited_user_has_admin_permission,
                            ),
                            rx.checkbox(
                                LS.maintainer_permission,
                                name="global_permission_maintainer",
                                default_checked=ManageUsersState.edited_user_has_maintainer_permission,
                            ),
                            rx.checkbox(
                                LS.lecturer_permission,
                                name="global_permission_lecturer",
                                default_checked=ManageUsersState.edited_user_has_lecturer_permission,
                            ),
                            align="start",
                            spacing="2",
                            width="100%",
                        ),
                        form_label(LS.enabled),
                        rx.checkbox(
                            name="enabled",
                            default_checked=local_user.enabled,
                        ),
                        # read-only information about the account
                        rx.vstack(
                            rx.hstack(
                                rx.text(LS.created_at + ":", size="2", weight="medium"),
                                rx.moment(
                                    user_info.created_at,
                                    format=gv.MOMENT_DATETIME_FORMAT,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.hstack(
                                rx.text(
                                    LS.last_login_at + ":", size="2", weight="medium"
                                ),
                                last_login_text(user_info),
                                spacing="2",
                                align="center",
                            ),
                            align="start",
                            spacing="1",
                            padding_top="1.5em",
                            width="100%",
                        ),
                        # buttons
                        rx.hstack(
                            rx.button(
                                LS.cancel,
                                variant="outline",
                                type="button",
                                on_click=ManageUsersState.close_edit_dialog(),
                                _hover={"cursor": "pointer"},
                            ),
                            rx.button(
                                LS.save,
                                type="submit",
                                loading=ManageUsersState.save_in_progress,
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
        ManageUsersState.edited_user != None,
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
                    rx.table.column_header_cell(LS.role),
                    rx.table.column_header_cell(LS.enabled),
                    rx.table.column_header_cell(LS.email_verified),
                    rx.table.column_header_cell(LS.created_at),
                    rx.table.column_header_cell(LS.last_login_at),
                    rx.table.column_header_cell(""),
                ),
            ),
            # dynamically render each new entry
            rx.table.body(rx.foreach(ManageUsersState.users, user_table_row)),
            variant="surface",
            size="3",
            width="85vw",
            overflow_x="auto",
            overflow_y="auto",
            max_height="66vh",
        ),
    )
