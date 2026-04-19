"""Components for the my lectures page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.language_state import LanguageState as LS
from aitutor.models import Lecture, LectureRole
from aitutor.pages.my_lectures.state import LectureWithRole, MyLecturesState


def lecture_role_text(role: int):
    """Convert a LectureRole to text in a way that works for Reflex."""
    return rx.match(
        role,
        (LectureRole.OWNER.value, LectureRole.OWNER.name),
        (LectureRole.TUTOR.value, LectureRole.TUTOR.name),
        (LectureRole.STUDENT.value, LectureRole.STUDENT.name),
        "Unknown",
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
        rx.table.cell(lecture_role_text(role)),
        rx.table.cell(
            rx.cond(
                role == LectureRole.OWNER.value,
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
    return rx.cond(
        MyLecturesState.joined_lectures,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(LS.lecture_name),
                    rx.table.column_header_cell(LS.role),
                    rx.table.column_header_cell(""),
                )
            ),
            rx.table.body(rx.foreach(MyLecturesState.joined_lectures, lecture_row)),
            variant="surface",
            size="3",
            width="85vw",
            max_width="100%",
        ),
        rx.text(LS.no_joined_lectures, size="4"),
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
