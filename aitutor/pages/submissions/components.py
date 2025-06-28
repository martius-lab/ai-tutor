"""Components for the submissions page."""

import reflex as rx

from aitutor.pages.submissions.state import SubmissionsState


def header_cell(text: str, icon: str):
    """Create header cells."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="3",
        ),
    )


def show_student(student_name: int):
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(student_name),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def submissions_table():
    """The main table"""
    return (
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    header_cell("Username", "user-round"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SubmissionsState.users_with_results,
                    lambda user_with_result: show_student(user_with_result[0].username),
                )
            ),
            variant="surface",
            size="3",
            width="85vw",
            overflow_y="auto",
            max_height="70vh",
        ),
    )
