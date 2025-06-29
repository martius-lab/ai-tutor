"""Components for the submissions page."""

import reflex as rx

from aitutor.pages.submissions.state import SubmissionsState
from reflex_local_auth.user import LocalUser


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


def show_student(table_row: tuple[LocalUser, str, bool]) -> rx.Component:
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(table_row[0].username),
        rx.table.cell(table_row[1]),
        rx.table.cell(
            rx.cond(
                table_row[2],
                rx.icon_button(
                    "search",
                    size="2",
                    color_scheme="iris",
                    on_click=rx.redirect(
                        f"{SubmissionsState.finished_view_teacher_url}/{table_row[0].id}"
                    ),
                    _hover={"cursor": "pointer"},
                ),
                "No submission",
            )
        ),
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
                    header_cell("Role", "shield_check"),
                    header_cell("Submission", "circle-check"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SubmissionsState.table_rows,
                    show_student,
                )
            ),
            variant="surface",
            size="3",
            width="85vw",
            overflow_y="auto",
            max_height="70vh",
        ),
    )
