"""Components for the lecture members page."""

import reflex as rx

import aitutor.routes as routes
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
        value=member["selected_role"],
        on_change=LectureMembersState.set_member_role(member["user_id"]),
        size="2",
    )


def editable_role_cell(member: LectureMemberRow) -> rx.Component:
    """Render role dropdown and row-local action buttons when changed."""
    return rx.vstack(
        role_select(member),
        rx.cond(
            member["role"] != member["selected_role"],
            rx.hstack(
                rx.button(
                    LS.cancel,
                    size="1",
                    variant="outline",
                    on_click=LectureMembersState.cancel_member_role_change(member["user_id"]),
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    LS.save,
                    size="1",
                    on_click=LectureMembersState.save_member_role_change(member["user_id"]),
                    _hover={"cursor": "pointer"},
                ),
                spacing="2",
            ),
        ),
        align="start",
        spacing="2",
    )


def back_to_overview_button() -> rx.Component:
    """Render a back button to the current lecture overview."""
    return rx.button(
        rx.icon("arrow-left", size=20),
        "Lecture Overview",
        on_click=rx.redirect(
            f"{routes.LECTURE_OVERVIEW}/{LectureMembersState.current_lecture_id}"
        ),
        _hover={"cursor": "pointer"},
    )


def members_header() -> rx.Component:
    """Render the members page header."""
    return rx.vstack(
        rx.hstack(
            back_to_overview_button(),
            width="85vw",
            max_width="100%",
        ),
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


def member_row(member: LectureMemberRow) -> rx.Component:
    """Render one lecture member row."""
    return rx.table.row(
        rx.table.cell(member["username"]),
        rx.table.cell(
            rx.cond(
                LectureMembersState.is_owner,
                editable_role_cell(member),
                rx.text(lecture_role_text(member["role"])),
            )
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