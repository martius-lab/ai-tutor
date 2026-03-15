"""Components for the token analyzer page."""

import reflex as rx

from aitutor.language_state import LanguageState
from aitutor.pages.token_analyzer.state import TableRow, TokenAnalyzerState


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
    """Show token usage in a table row."""
    return rx.table.row(
        rx.table.cell(table_row.username),
        rx.table.cell(table_row.tokens_used),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def token_analyzer_table() -> rx.Component:
    """The main token analyzer table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                header_cell(LanguageState.user, "user-round"),
                header_cell(LanguageState.token_usage, "chart-column"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                TokenAnalyzerState.table_rows,
                show_table_row,
            )
        ),
        variant="surface",
        size="3",
        width="85vw",
        overflow_y="auto",
        max_height="60vh",
    )
