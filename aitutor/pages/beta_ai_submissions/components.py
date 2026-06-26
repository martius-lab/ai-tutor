"""Components for the Beta AI submissions page."""

import reflex as rx

from aitutor import routes
from aitutor.pages.beta_ai_submissions.state import (
    BetaAISubmissionsState,
    BetaSubmissionRow,
)


def header_cell(text: str, icon: str) -> rx.Component:
    """Create a table header cell."""
    return rx.table.column_header_cell(
        rx.hstack(rx.icon(icon, size=18), rx.text(text), align="center", spacing="3")
    )


def show_table_row(row: BetaSubmissionRow) -> rx.Component:
    """Render one Beta AI submission row."""
    return rx.table.row(
        rx.table.cell(row.username),
        rx.table.cell(row.exercise_title),
        rx.table.cell(
            rx.cond(
                row.has_submitted,
                rx.icon_button(
                    "search",
                    size="2",
                    on_click=rx.redirect(
                        f"{routes.BETA_AI_FINISHED_VIEW_TUTOR}/{row.beta_exercise_id}/{row.user_id}"
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.text("Not submitted"),
            )
        ),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def beta_ai_submissions_table() -> rx.Component:
    """Render the Beta AI submissions table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                header_cell("User", "user-round"),
                header_cell("Beta AI Exercise", "book"),
                header_cell("Submission", "circle-check"),
            )
        ),
        rx.table.body(rx.foreach(BetaAISubmissionsState.table_rows, show_table_row)),
        variant="surface",
        size="3",
        width="85vw",
        overflow_y="auto",
        max_height="60vh",
    )


def beta_ai_submissions_content() -> rx.Component:
    """Render the Beta AI submissions page content."""
    return rx.vstack(
        rx.heading("Beta AI Submissions", size="7"),
        rx.cond(
            BetaAISubmissionsState.table_rows.length() == 0,  # type: ignore
            rx.callout(
                "No submitted Beta AI exercises yet.", icon="info", width="100%"
            ),
            beta_ai_submissions_table(),
        ),
        align="center",
        spacing="4",
        width="100%",
    )
