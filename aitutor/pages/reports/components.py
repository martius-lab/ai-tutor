"""Components for the reports page."""

import reflex as rx

from aitutor import routes
from aitutor.components.dialogs import destructive_confirm
from aitutor.global_vars import (
    SEARCH_EXERCISE_KEY,
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
                color=rx.color("black", 11),
                style={
                    "white-space": "nowrap",
                    "overflow": "hidden",
                    "text-overflow": "ellipsis",
                    "max-width": "200px",
                },
            )
        ),
        rx.table.cell(
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.icon_button(
                        rx.cond(
                            table_row.looked_at,
                            rx.icon("mail-open", size=22),
                            rx.icon("mail", size=22),
                        ),
                        size="2",
                        color_scheme=rx.cond(
                            table_row.looked_at,
                            "gray",
                            "blue",
                        ),
                        variant="ghost",
                        on_click=ReportsState.toggle_looked_at(
                            table_row.report_id
                            if table_row.report_id is not None
                            else 0
                        ),
                        _hover={"cursor": "pointer"},
                    )
                ),
                rx.hover_card.content(
                    rx.text(
                        rx.cond(
                            table_row.looked_at,
                            LanguageState.report_seen_tooltip,
                            LanguageState.report_not_seen_tooltip,
                        )
                    ),
                ),
            )
        ),
        rx.table.cell(
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.icon_button(
                        "search",
                        size="2",
                        color_scheme="iris",
                        on_click=rx.redirect(
                            f"{routes.REPORT_VIEW}/{table_row.report_id}"
                        ),
                        _hover={"cursor": "pointer"},
                    )
                ),
                rx.hover_card.content(
                    rx.text(LanguageState.report_view_tooltip),
                ),
            )
        ),
        rx.table.cell(
            destructive_confirm(
                title=LanguageState.delete_report_title,
                description=LanguageState.delete_report_content,
                confirm_text=LanguageState.delete,
                cancel_text=LanguageState.cancel,
                on_confirm=ReportsState.delete_report(
                    table_row.report_id if table_row.report_id is not None else 0
                ),
                trigger=rx.icon_button(
                    rx.icon("trash"),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    _hover={"cursor": "pointer"},
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
                header_cell(LanguageState.reports, "flag"),
                header_cell("Status", "mail"),
                header_cell(LanguageState.report_view, "search"),
                header_cell(LanguageState.delete, "trash"),
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
