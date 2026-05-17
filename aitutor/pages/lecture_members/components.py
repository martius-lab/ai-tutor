"""Components for the lecture members page."""

import reflex as rx

from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState as LS
from aitutor.models import LectureRole
from aitutor.pages.lecture_members.state import LectureMemberRow, LectureMembersState


def lecture_role_text(role: str):
    """Convert a lecture role value to localized text."""
    return rx.match(
        role,
        (LectureRole.OWNER.name, LS.owner_role),
        (LectureRole.TUTOR.name, LS.tutor_role),
        (LectureRole.STUDENT.name, LS.student_role),
        LS.student_role,
    )


def role_select(member: LectureMemberRow) -> rx.Component:
    """Render the owner-only role dropdown for one member."""
    return rx.select(
        (
            LectureRole.STUDENT.name,
            LectureRole.TUTOR.name,
            LectureRole.OWNER.name,
        ),
        value=member.selected_role,
        on_change=LectureMembersState.set_member_role(member.user_id),
        size="2",
    )


def editable_role_cell(member: LectureMemberRow) -> rx.Component:
    """Render role dropdown and row-local action buttons when changed."""
    return rx.vstack(
        role_select(member),
        rx.cond(
            member.role != member.selected_role,
            rx.hstack(
                rx.button(
                    LS.cancel,
                    size="1",
                    variant="outline",
                    on_click=LectureMembersState.cancel_member_role_change(
                        member.user_id
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    LS.save,
                    size="1",
                    on_click=LectureMembersState.save_member_role_change(
                        member.user_id
                    ),
                    _hover={"cursor": "pointer"},
                ),
                spacing="2",
            ),
        ),
        align="start",
        spacing="2",
    )


def members_header() -> rx.Component:
    """Render the members page header."""
    return rx.vstack(
        rx.hstack(
            rx.heading("Members", size="5"),
            rx.cond(
                LectureMembersState.lecture_name != "",
                rx.text(LectureMembersState.lecture_name, color_scheme="gray"),
            ),
            align="baseline",
            width="85vw",
            max_width="100%",
        ),
        spacing="3",
        align="center",
        width="100%",
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
        LectureMembersState.members,
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
            rx.table.body(rx.foreach(LectureMembersState.members, member_row)),
            variant="surface",
            size="3",
            width="85vw",
            max_width="100%",
            overflow_y="auto",
            max_height="66vh",
        ),
        rx.center(
            rx.text("No members found.", size="4"),
            width="85vw",
            max_width="100%",
        ),
    )


def lecture_members_content() -> rx.Component:
    """Main content for the lecture members page."""
    return rx.vstack(
        members_header(),
        members_table(),
        spacing="3",
        align="center",
        width="100%",
    )
