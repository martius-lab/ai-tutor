"""Components for the submissions page."""

import reflex as rx

from aitutor.pages.submissions.state import SubmissionsState, TableRow
from aitutor import routes


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


def show_student(table_row: TableRow) -> rx.Component:
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(table_row.username),
        rx.table.cell(table_row.exercise_title),
        rx.table.cell(
            rx.hstack(
                rx.foreach(
                    table_row.exercise_tags,
                    lambda tag: rx.badge(
                        tag,
                        variant="soft",
                        color_scheme="blue",
                        on_click=SubmissionsState.add_search_value(
                            {"search_value": tag}
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                spacing="1",
                wrap="wrap",
            )
        ),
        rx.table.cell(
            rx.cond(
                table_row.has_submitted,
                rx.icon_button(
                    "search",
                    size="2",
                    color_scheme="iris",
                    on_click=rx.redirect(
                        f"{routes.FINISHED_VIEW_TEACHER}/{table_row.exercise_id}/{table_row.user_id}"
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
                    header_cell("Exercise", "book"),
                    header_cell("Tags", "tag"),
                    header_cell("Submission", "circle-check"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SubmissionsState.rendered_table_rows,
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


def search_badges() -> rx.Component:
    """Display search badges for the current search values."""
    return rx.hstack(
        rx.foreach(
            SubmissionsState.search_values,
            lambda value: rx.badge(
                rx.hstack(
                    rx.text(value),
                    rx.icon(
                        "x",
                        on_click=SubmissionsState.remove_search_value(value),
                        _hover={"cursor": "pointer"},
                    ),
                    spacing="1",
                    align="center",
                ),
                variant="solid",
                color_scheme="blue",
            ),
        ),
        spacing="2",
        wrap="wrap",
    )
