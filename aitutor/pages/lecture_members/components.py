"""Components for the lecture members page."""

import reflex as rx

from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState as LS
from aitutor.models import LectureRole
from aitutor.pages.lecture_members.state import (
    AvailableLectureUser,
    LectureMemberRow,
    LectureMembersState,
)


def lecture_role_text(role: rx.Var[str] | str):
    """Convert a lecture role value to localized text."""
    return rx.match(
        role,
        (LectureRole.OWNER.name, LS.owner_role),
        (LectureRole.TUTOR.name, LS.tutor_role),
        (LectureRole.STUDENT.name, LS.student_role),
        LS.student_role,
    )


def editable_role_cell(member: LectureMemberRow) -> rx.Component:
    """Render role text and an edit icon button to open the edit role dialog."""
    return rx.hstack(
        rx.text(lecture_role_text(member.role)),
        rx.cond(
            LectureMembersState.can_manage_members,
            rx.icon_button(
                "pencil",
                size="1",
                variant="ghost",
                on_click=LectureMembersState.open_edit_role_dialog(member.user_id),
                _hover={"cursor": "pointer"},
            ),
        ),
        align="center",
        spacing="2",
    )


def members_header() -> rx.Component:
    """Render the members page header."""
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading(LS.members, size="5"),
                rx.cond(
                    LectureMembersState.lecture_name != "",
                    rx.text(LectureMembersState.lecture_name, color_scheme="gray"),
                ),
                align="baseline",
            ),
            rx.cond(
                LectureMembersState.can_manage_members,
                add_member_dialog(),
            ),
            justify="between",
            align="center",
            width="85vw",
            max_width="100%",
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def add_member_dialog() -> rx.Component:
    """Render the dialog for adding users to the lecture."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.flex(
                    rx.icon("user-plus", size=15),
                    LS.add_member,
                    gap="0.5em",
                    align="center",
                ),
                on_click=LectureMembersState.open_add_member_dialog,
                _hover={"cursor": "pointer"},
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(LS.add_member),
                rx.dialog.description(LS.add_member_description),
                available_user_filter(),
                available_users_list(),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            LS.close,
                            variant="outline",
                            on_click=LectureMembersState.close_add_member_dialog,
                            _hover={"cursor": "pointer"},
                        )
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                align="stretch",
            ),
            max_width="34em",
        ),
        open=LectureMembersState.add_member_dialog_is_open,
        on_open_change=LectureMembersState.set_add_member_dialog_is_open,
    )


def available_user_filter() -> rx.Component:
    """Render the search field for available users."""
    return rx.hstack(
        rx.input(
            value=LectureMembersState.available_user_filter_query,
            on_change=LectureMembersState.set_available_user_filter_query,
            placeholder=LS.search_filter_placeholder,
            width="100%",
        ),
        rx.cond(
            LectureMembersState.available_user_filter_query != "",
            rx.button(
                "×",
                on_click=LectureMembersState.clear_available_user_filter_query,
                variant="soft",
                size="2",
                _hover={"cursor": "pointer"},
            ),
        ),
        align="center",
        width="100%",
    )


def available_user_row(user: AvailableLectureUser) -> rx.Component:
    """Render one available user row in the add-member dialog."""
    return rx.hstack(
        rx.text(user.username),
        rx.button(
            rx.flex(
                rx.icon("user-plus", size=14),
                LS.add,
                gap="0.4em",
                align="center",
            ),
            size="2",
            on_click=LectureMembersState.add_member(user.user_id),
            _hover={"cursor": "pointer"},
        ),
        justify="between",
        align="center",
        width="100%",
        padding="0.5em",
        border_bottom=f"1px solid {rx.color('gray', 5)}",
    )


def available_users_list() -> rx.Component:
    """Render the filtered list of users that can be added."""
    return rx.cond(
        LectureMembersState.filtered_available_users,
        rx.vstack(
            rx.foreach(
                LectureMembersState.filtered_available_users,
                available_user_row,
            ),
            spacing="0",
            align="stretch",
            width="100%",
            max_height="20em",
            overflow_y="auto",
            border=f"1px solid {rx.color('gray', 5)}",
            border_radius="0.5em",
        ),
        rx.center(
            rx.text(LS.no_available_users, color_scheme="gray"),
            width="100%",
            padding="1em",
        ),
    )


def kick_member_button(member: LectureMemberRow) -> rx.Component:
    """Render the kick button with a destructive confirmation dialog."""
    return destructive_confirm(
        title=LS.kick + ": " + member.username,
        description=LS.kick_member_description,
        confirm_text=LS.kick,
        cancel_text=LS.cancel,
        on_confirm=LectureMembersState.kick_member(member.user_id),
        trigger=rx.button(
            rx.flex(
                LS.kick,
                gap="0.5em",
                align="center",
            ),
            color_scheme="red",
            variant="outline",
            size="2",
            _hover={"cursor": "pointer"},
        ),
    )


def member_row(member: LectureMemberRow) -> rx.Component:
    """Render one lecture member row."""
    return rx.table.row(
        rx.table.cell(member.username),
        rx.table.cell(
            rx.cond(
                LectureMembersState.can_manage_members,
                editable_role_cell(member),
                rx.text(lecture_role_text(member.role)),
            )
        ),
        rx.cond(
            LectureMembersState.can_manage_members,
            rx.table.cell(kick_member_button(member)),
        ),
    )


def members_table() -> rx.Component:
    """Render the table containing all loaded lecture members."""
    return rx.cond(
        LectureMembersState.member_list,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(LS.username),
                    rx.table.column_header_cell(LS.role),
                    rx.cond(
                        LectureMembersState.can_manage_members,
                        rx.table.column_header_cell(""),
                    ),
                )
            ),
            rx.table.body(rx.foreach(LectureMembersState.member_list, member_row)),
            variant="surface",
            size="3",
            width="85vw",
            max_width="100%",
            overflow_y="auto",
            max_height="66vh",
        ),
        rx.center(
            rx.text(LS.no_members_found, size="4"),
            width="85vw",
            max_width="100%",
        ),
    )


def edit_role_dialog() -> rx.Component:
    """Render the edit role dialog."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                LectureMembersState.editing_member,
                rx.vstack(
                    rx.dialog.title(
                        LectureMembersState.edit_role_title,
                        size="5",
                        weight="bold",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text(LS.label_new_role),
                            rx.select(
                                items=LectureMembersState.role_option_labels,
                                value=LectureMembersState.selected_role_option,
                                on_change=LectureMembersState.set_editing_member_role,
                                size="2",
                            ),
                            align="center",
                            spacing="2",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.markdown(
                            LS.roles_description,
                            font_size="0.9em",
                            color=rx.color("gray", 11),
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            LS.cancel,
                            size="3",
                            variant="outline",
                            on_click=LectureMembersState.close_edit_role_dialog,
                            _hover={"cursor": "pointer"},
                        ),
                        rx.button(
                            LS.save,
                            size="3",
                            disabled=~LectureMembersState.editing_member_has_changes,
                            on_click=LectureMembersState.save_editing_member_role,
                            _hover=rx.cond(
                                LectureMembersState.editing_member_has_changes,
                                {"cursor": "pointer"},
                                {"cursor": "not-allowed"},
                            ),
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                ),
            ),
        ),
        open=LectureMembersState.edit_role_dialog_is_open,
        on_open_change=LectureMembersState.set_edit_role_dialog_is_open,
    )


def lecture_members_content() -> rx.Component:
    """Main content for the lecture members page."""
    return rx.vstack(
        members_header(),
        members_table(),
        rx.cond(LectureMembersState.can_manage_members, edit_role_dialog()),
        spacing="3",
        align="center",
        width="100%",
    )
