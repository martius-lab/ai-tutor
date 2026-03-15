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


def token_analyzer_bar_chart() -> rx.Component:
    """Bar chart showing token usage by user rank."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(
                    data_key="rank",
                    ticks=TokenAnalyzerState.chart_ticks,
                    interval=0,
                    label={"value": "User-Rank", "position": "insideBottom", "offset": -2},
                ),
                rx.recharts.y_axis(
                    label={
                        "value": LanguageState.token_usage,
                        "angle": -90,
                        "position": "insideLeft",
                    }
                ),
                rx.recharts.graphing_tooltip(),
                rx.recharts.bar(
                    data_key="tokens_used",
                    fill=rx.color("indigo", 8),
                    bar_size=3,
                ),
                data=TokenAnalyzerState.chart_data,
                margin={"top": 8, "right": 16, "left": 16, "bottom": 24},
            ),
            width="100%",
            height=320,
            min_width=TokenAnalyzerState.chart_min_width,
        ),
        width="85vw",
        overflow_x="auto",
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
