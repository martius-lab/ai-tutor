"""Components for the reports page."""

import reflex as rx
from aitutor.pages.reports.state import ReportsState

def header_cell(text: str):
    """Create header cells for the table."""
    return rx.table.column_header_cell(
        rx.text(text, align="center")
    )

def show_table_row(report) -> rx.Component:
    """Render one report in a table row."""
    return rx.table.row(
        rx.table.cell(report.id),
        rx.table.cell(report.exercise_result_id),
        rx.table.cell(report.report_text),
        rx.table.cell(
            rx.cond(
                report.looked_at,
                "Yes",
                "No"
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
                header_cell("ID"),
                header_cell("Exercise Result"),
                header_cell("Text"),
                header_cell("Looked At"),
            )
        ),
        rx.table.body(
            rx.foreach(
                ReportsState.reports,
                show_table_row
            )
        ),
        variant="surface",
        size="3",
        width="85vw",
        overflow_y="auto",
        max_height="60vh",
    )


