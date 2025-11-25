"""Components for the reports page."""

import reflex as rx

from aitutor import routes
from aitutor.global_vars import (
    SEARCH_EXERCISE_KEY,
    SEARCH_TAG_KEY,
    SEARCH_USER_KEY,
)
from aitutor.language_state import LanguageState
from aitutor.pages.reports.state import ReportsState, TableRow


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
    """Show reports in a table row."""
    return rx.table.row(
        rx.table.cell(
            table_row.username,
            on_click=ReportsState.add_search_value(
                {"search_value": f'{SEARCH_USER_KEY}:"{table_row.username}"'}
            ),
            _hover={"cursor": "pointer"},
        ),
        rx.table.cell(
            table_row.exercise_title,
            on_click=ReportsState.add_search_value(
                {"search_value": f'{SEARCH_EXERCISE_KEY}:"{table_row.exercise_title}"'}
            ),
            _hover={"cursor": "pointer"},
        ),
        rx.table.cell(
            rx.text(
                table_row.report_preview,
                color=rx.color("red", 11),
                style={
                    "white-space": "nowrap",
                    "overflow": "hidden",
                    "text-overflow": "ellipsis",
                    "max-width": "200px",
                },
            )
        ),
        rx.table.cell(
            rx.icon_button(
                rx.cond(
                    table_row.looked_at,
                    rx.icon("mail-open", size=18),
                    rx.icon("mail", size=18),
                ),
                size="2",
                color_scheme=rx.cond(
                    table_row.looked_at,
                    "gray",
                    "blue",
                ),
                variant="soft",
                on_click=ReportsState.toggle_looked_at(table_row.report_id),
                _hover={"cursor": "pointer"},
            )
        ),
        rx.table.cell(
            rx.icon_button(
                "eye",
                size="2",
                color_scheme="iris",
                on_click=rx.redirect(
                    f"{routes.REPORT_VIEW}/{table_row.report_id}"
                ),
                _hover={"cursor": "pointer"},
            )
        ),
        rx.table.cell(
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.icon_button(
                        "trash-2",
                        size="2",
                        color_scheme="red",
                        variant="soft",
                        _hover={"cursor": "pointer"},
                    )
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Delete Report"),
                    rx.alert_dialog.description(
                        "Are you sure you want to delete this report? This action cannot be undone."
                    ),
                    rx.hstack(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "Cancel",
                                color_scheme="gray",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Delete",
                                color_scheme="red",
                                on_click=ReportsState.delete_report(table_row.report_id),
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        margin_top="1em",
                    ),
                ),
            )
        ),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def reports_table():
    """The main table showing all reports."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                header_cell(LanguageState.user, "user-round"),
                header_cell(LanguageState.exercise, "book"),
                header_cell("Report", "flag"),
                header_cell("Status", "mail"),
                header_cell("View", "eye"),
                header_cell("Delete", "trash-2"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                ReportsState.table_rows,
                show_table_row,
            )
        ),
        variant="surface",
        size="3",
        width="85vw",
        overflow_y="auto",
        max_height="60vh",
    )
