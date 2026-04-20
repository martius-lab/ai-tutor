"""Components for the my lectures page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState as LS
from aitutor.models import Lecture, LectureRole
from aitutor.pages.my_lectures.state import LectureWithRole, MyLecturesState


def lecture_role_text(role: int | None):
    """Convert a LectureRole to text in a way that works for Reflex."""
    return rx.cond(
        role is None,
        LS.not_joined,
        rx.match(
            role,
            (LectureRole.OWNER.value, LS.owner_role),
            (LectureRole.TUTOR.value, LS.tutor_role),
            (LectureRole.STUDENT.value, LS.student_role),
            LS.not_joined,
        ),
    )


def role_filter_button(label, value: str) -> rx.Component:
    """Render a small role filter button."""
    return rx.button(
        label,
        variant=rx.cond(MyLecturesState.role_filter == value, "solid", "outline"),
        size="2",
        on_click=MyLecturesState.set_role_filter(value),
        _hover={"cursor": "pointer"},
    )


def role_filter_text(label, value) -> rx.Component:
    """Render clickable role text without badge styling."""
    return rx.text(
        label,
        on_click=MyLecturesState.set_role_filter(value),
        _hover={"cursor": "pointer"},
    )


def role_filter_value(role: int | None):
    """Return the filter value for a role."""
    return rx.cond(
        role == LectureRole.OWNER.value,
        "owner",
        rx.cond(
            role == LectureRole.TUTOR.value,
            "tutor",
            rx.cond(
                role == LectureRole.STUDENT.value,
                "student",
                "not_joined",
            ),
        ),
    )


def add_lecture_button() -> rx.Component:
    """Button for creating a new lecture."""
    return rx.cond(
        MyLecturesState.can_create_lectures,
        rx.link(
            rx.button(
                rx.flex(rx.icon("plus", size=15), LS.add, gap="0.5em", align="center"),
                _hover={"cursor": "pointer"},
            ),
            href=routes.EDIT_LECTURE + "/new",
        ),
    )


def lecture_row(joined_lecture: LectureWithRole) -> rx.Component:
    """Render a single joined lecture row."""
    lecture: Lecture = joined_lecture[0]
    role = joined_lecture[1]

    return rx.table.row(
        rx.table.cell(lecture.lecture_name),
        rx.table.cell(
            role_filter_text(
                lecture_role_text(role),
                role_filter_value(role),
            )
        ),
        rx.table.cell(
            rx.cond(
                (role == LectureRole.OWNER.value) | MyLecturesState.is_global_admin,
                rx.link(
                    rx.button(
                        rx.flex(
                            rx.icon("pen", size=15),
                            LS.edit,
                            gap="0.5em",
                            align="center",
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                    href=f"{routes.EDIT_LECTURE}/{lecture.id}",
                ),
            )
        ),
    )


def my_lectures_table() -> rx.Component:
    """Table of all lectures joined by the current user."""
    return rx.vstack(
        rx.hstack(
            rx.input(
                value=MyLecturesState.search_text,
                placeholder=LS.search_placeholder,
                on_change=MyLecturesState.update_search_text,
                width="22em",
                max_width="100%",
            ),
            role_filter_button(LS.all, "all"),
            role_filter_button(LS.owner_role, "owner"),
            role_filter_button(LS.tutor_role, "tutor"),
            role_filter_button(LS.student_role, "student"),
            rx.cond(
                MyLecturesState.is_global_admin,
                role_filter_button(LS.not_joined, "not_joined"),
            ),
            wrap="wrap",
            width="85vw",
            max_width="100%",
        ),
        rx.cond(
            MyLecturesState.filtered_lectures,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(LS.lecture_name),
                        rx.table.column_header_cell(LS.role),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(MyLecturesState.filtered_lectures, lecture_row)
                ),
                variant="surface",
                size="3",
                width="85vw",
                max_width="100%",
                overflow_y="auto",
                max_height="66vh",
            ),
            rx.cond(
                MyLecturesState.joined_lectures,
                rx.text(LS.no_matching_lectures, size="4"),
                rx.text(LS.no_joined_lectures, size="4"),
            ),
        ),
        spacing="3",
    )


def my_lectures_content() -> rx.Component:
    """Main content for the my lectures page."""
    return rx.vstack(
        rx.hstack(
            rx.heading(LS.my_lectures, size="6"),
            add_lecture_button(),
            justify="between",
            align="center",
            width="85vw",
            max_width="100%",
        ),
        my_lectures_table(),
        spacing="3",
        align="center",
        width="100%",
    )
