"""Components for the submissions page."""

import reflex as rx

from aitutor.pages.submissions.state import SubmissionsState, TableRow
from aitutor import routes
from aitutor.global_vars import (
    SEARCH_USER_KEY,
    SEARCH_EXERCISE_KEY,
    SEARCH_TAG_KEY,
)
from aitutor.language_state import LanguageState


def header_cell(text, icon: str):
    """Create header cells."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="3",
        ),
    )


def show_table_row(table_row: TableRow) -> rx.Component:
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(
            table_row.username,
            on_click=SubmissionsState.add_search_value(
                {"search_value": f'{SEARCH_USER_KEY}:"{table_row.username}"'}
            ),
            _hover={"cursor": "pointer"},
        ),
        rx.table.cell(
            table_row.exercise_title,
            on_click=SubmissionsState.add_search_value(
                {"search_value": f'{SEARCH_EXERCISE_KEY}:"{table_row.exercise_title}"'}
            ),
            _hover={"cursor": "pointer"},
        ),
        rx.table.cell(
            rx.hstack(
                rx.foreach(
                    table_row.exercise_tags,
                    lambda tag: rx.badge(
                        tag,
                        variant="soft",
                        color_scheme="blue",
                        on_click=SubmissionsState.add_search_value(
                            {"search_value": f'{SEARCH_TAG_KEY}:"{tag}"'}
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
                        f"{routes.FINISHED_VIEW_TUTOR}/{table_row.exercise_id}/{table_row.user_id}"
                    ),
                    _hover={"cursor": "pointer"},
                ),
                LanguageState.no_submission,
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
                    header_cell(LanguageState.user, "user-round"),
                    header_cell(LanguageState.exercise, "book"),
                    header_cell(LanguageState.tags, "tag"),
                    header_cell(LanguageState.submission, "circle-check"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SubmissionsState.table_rows,
                    show_table_row,
                )
            ),
            variant="surface",
            size="3",
            width="85vw",
            overflow_y="auto",
            max_height="60vh",
        ),
    )
