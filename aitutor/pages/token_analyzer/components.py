"""Components for the token analyzer page."""

import reflex as rx

from aitutor.language_state import LanguageState
from aitutor.pages.token_analyzer.state import (
    ALL_EXERCISES_OPTION,
    ALL_USERS_OPTION,
    EXERCISE_ANALYSIS_VIEW,
    ExerciseTableRow,
    TableRow,
    TokenAnalyzerState,
    USER_ANALYSIS_VIEW,
)


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
        rx.table.cell(table_row.rank),
        rx.table.cell(table_row.username),
        rx.table.cell(table_row.tokens_used),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def token_analyzer_exercise_selector() -> rx.Component:
    """Selector for filtering token analysis by exercise."""
    return rx.hstack(
        rx.text(
            LanguageState.exercise + ":",
            size="3",
            weight="medium",
        ),
        rx.input(
            value=TokenAnalyzerState.exercise_filter_query,
            on_change=TokenAnalyzerState.set_exercise_filter_query,
            placeholder="Starts with...",
            width="260px",
        ),
        rx.cond(
            TokenAnalyzerState.exercise_filter_query != "",
            rx.button(
                "×",
                on_click=TokenAnalyzerState.clear_exercise_filter_query,
                variant="soft",
                size="1",
            ),
            rx.box(width="26px"),
        ),
        rx.select(
            items=TokenAnalyzerState.filtered_exercise_options,
            value=TokenAnalyzerState.selected_exercise_name,
            on_change=TokenAnalyzerState.set_selected_exercise_name,
            placeholder=ALL_EXERCISES_OPTION,
            width="320px",
        ),
        align="center",
        width="85vw",
        justify="start",
    )


def token_analyzer_view_menu() -> rx.Component:
    """Menu to switch between user and exercise analysis views."""
    return rx.hstack(
        rx.text("View:", size="3", weight="medium"),
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.cond(
                        TokenAnalyzerState.active_analysis_view == USER_ANALYSIS_VIEW,
                        "User Stats",
                        "Exercise Stats",
                    ),
                    rx.icon("chevron-down", size=16),
                    variant="outline",
                    _hover={"cursor": "pointer"},
                )
            ),
            rx.menu.content(
                rx.menu.item(
                    "User Stats",
                    on_click=TokenAnalyzerState.set_active_analysis_view(
                        USER_ANALYSIS_VIEW
                    ),
                ),
                rx.menu.item(
                    "Exercise Stats",
                    on_click=TokenAnalyzerState.set_active_analysis_view(
                        EXERCISE_ANALYSIS_VIEW
                    ),
                ),
            ),
        ),
        width="85vw",
        justify="start",
        align="center",
    )


def token_analyzer_user_selector() -> rx.Component:
    """Selector for filtering exercise analysis by user."""
    return rx.hstack(
        rx.text(
            LanguageState.user + ":",
            size="3",
            weight="medium",
        ),
        rx.input(
            value=TokenAnalyzerState.user_filter_query,
            on_change=TokenAnalyzerState.set_user_filter_query,
            placeholder="Starts with...",
            width="260px",
        ),
        rx.cond(
            TokenAnalyzerState.user_filter_query != "",
            rx.button(
                "×",
                on_click=TokenAnalyzerState.clear_user_filter_query,
                variant="soft",
                size="1",
            ),
            rx.box(width="26px"),
        ),
        rx.select(
            items=TokenAnalyzerState.filtered_user_options,
            value=TokenAnalyzerState.selected_user_name,
            on_change=TokenAnalyzerState.set_selected_user_name,
            placeholder=ALL_USERS_OPTION,
            width="320px",
        ),
        align="center",
        width="85vw",
        justify="start",
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
                    label={"value": "User-Rank", "position": "insideBottom", "offset": -12},
                    min_tick_gap=8,
                ),
                rx.recharts.y_axis(
                    data_key="tokens_used_k",
                    width=100,
                    tick_count=6,
                    label={
                        "value": f"{LanguageState.token_usage} (K)",
                        "angle": -90,
                        "position": "outsideLeft",
                        "offset": 22,
                    },
                ),
                rx.recharts.graphing_tooltip(
                    separator=": ",
                ),
                rx.recharts.bar(
                    data_key="tokens_used_k",
                    name=LanguageState.token_usage,
                    fill=rx.color("indigo", 8),
                    bar_size=TokenAnalyzerState.user_bar_size,
                ),
                rx.recharts.bar(
                    data_key="username",
                    name=LanguageState.user,
                    fill="transparent",
                    bar_size=0,
                ),
                data=TokenAnalyzerState.chart_data,
                margin={"top": 8, "right": 16, "left": 56, "bottom": 24},
            ),
            width="100%",
            height=320,
            min_width=TokenAnalyzerState.chart_min_width,
        ),
        width="85vw",
        overflow_x="auto",
    )


def token_analyzer_exercise_bar_chart() -> rx.Component:
    """Bar chart showing token usage by exercise rank."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(
                    data_key="rank",
                    ticks=TokenAnalyzerState.exercise_chart_ticks,
                    interval=0,
                    label={
                        "value": "Exercise-Rank",
                        "position": "insideBottom",
                        "offset": -12,
                    },
                    min_tick_gap=8,
                ),
                rx.recharts.y_axis(
                    data_key="tokens_used_k",
                    width=100,
                    tick_count=6,
                    label={
                        "value": f"{LanguageState.token_usage} (K)",
                        "angle": -90,
                        "position": "outsideLeft",
                        "offset": 22,
                    },
                ),
                rx.recharts.graphing_tooltip(
                    separator=": ",
                ),
                rx.recharts.bar(
                    data_key="exercise",
                    name=LanguageState.exercise,
                    fill="transparent",
                    bar_size=0,
                ),
                rx.recharts.bar(
                    data_key="tokens_used_k",
                    name=LanguageState.token_usage,
                    fill=rx.color("cyan", 8),
                    bar_size=TokenAnalyzerState.exercise_bar_size,
                ),
                data=TokenAnalyzerState.exercise_chart_data,
                margin={"top": 8, "right": 16, "left": 56, "bottom": 24},
            ),
            width="100%",
            height=320,
            min_width=TokenAnalyzerState.exercise_chart_min_width,
        ),
        width="85vw",
        overflow_x="auto",
    )


def token_analyzer_table() -> rx.Component:
    """The main token analyzer table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                header_cell(LanguageState.rank, "hash"),
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


def show_exercise_table_row(table_row: ExerciseTableRow) -> rx.Component:
    """Show token usage in an exercise table row."""
    return rx.table.row(
        rx.table.cell(table_row.rank),
        rx.table.cell(table_row.exercise_title),
        rx.table.cell(table_row.tokens_used),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def token_analyzer_exercise_table() -> rx.Component:
    """Exercise-focused token analyzer table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                header_cell(LanguageState.rank, "hash"),
                header_cell(LanguageState.exercise, "book-open-check"),
                header_cell(LanguageState.token_usage, "chart-column"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                TokenAnalyzerState.exercise_table_rows,
                show_exercise_table_row,
            )
        ),
        variant="surface",
        size="3",
        width="85vw",
        overflow_y="auto",
        max_height="60vh",
    )
