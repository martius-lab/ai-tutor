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

# Invisible prefixes used only to keep tooltip row ordering stable across translations.
TOOLTIP_PREFIX_PRIMARY = "\u200b"
TOOLTIP_PREFIX_SECONDARY = "\u200c"


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


def analyzer_filter_selector(
    label_text,
    query_value,
    on_query_change,
    on_query_clear,
    options,
    selected_value,
    on_select_change,
    placeholder,
) -> rx.Component:
    """Reusable selector row with prefix-search input and clear button."""
    return rx.hstack(
        rx.text(
            label_text + ":",
            size="3",
            weight="medium",
        ),
        rx.input(
            value=query_value,
            on_change=on_query_change,
            placeholder=LanguageState.starts_with_placeholder,
            width="260px",
        ),
        rx.cond(
            query_value != "",
            rx.button(
                "×",
                on_click=on_query_clear,
                variant="soft",
                size="1",
            ),
            rx.box(width="26px"),
        ),
        rx.select(
            items=options,
            value=selected_value,
            on_change=on_select_change,
            placeholder=placeholder,
            width="320px",
        ),
        align="center",
        width="85vw",
        justify="start",
    )


def token_analyzer_exercise_selector() -> rx.Component:
    """Selector for filtering token analysis by exercise."""
    return analyzer_filter_selector(
        label_text=LanguageState.exercise,
        query_value=TokenAnalyzerState.exercise_filter_query,
        on_query_change=TokenAnalyzerState.set_exercise_filter_query,
        on_query_clear=TokenAnalyzerState.clear_exercise_filter_query,
        options=TokenAnalyzerState.filtered_exercise_options,
        selected_value=TokenAnalyzerState.selected_exercise_name,
        on_select_change=TokenAnalyzerState.set_selected_exercise_name,
        placeholder=ALL_EXERCISES_OPTION,
    )


def token_analyzer_view_menu() -> rx.Component:
    """Menu to switch between user and exercise analysis views."""
    return rx.hstack(
        rx.text(LanguageState.view + ":", size="3", weight="medium"),
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.cond(
                        TokenAnalyzerState.active_analysis_view == USER_ANALYSIS_VIEW,
                        LanguageState.user_stats,
                        LanguageState.exercise_stats,
                    ),
                    rx.icon("chevron-down", size=16),
                    variant="outline",
                    _hover={"cursor": "pointer"},
                )
            ),
            rx.menu.content(
                rx.menu.item(
                    LanguageState.user_stats,
                    on_click=TokenAnalyzerState.set_active_analysis_view(
                        USER_ANALYSIS_VIEW
                    ),
                ),
                rx.menu.item(
                    LanguageState.exercise_stats,
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
    return analyzer_filter_selector(
        label_text=LanguageState.user,
        query_value=TokenAnalyzerState.user_filter_query,
        on_query_change=TokenAnalyzerState.set_user_filter_query,
        on_query_clear=TokenAnalyzerState.clear_user_filter_query,
        options=TokenAnalyzerState.filtered_user_options,
        selected_value=TokenAnalyzerState.selected_user_name,
        on_select_change=TokenAnalyzerState.set_selected_user_name,
        placeholder=ALL_USERS_OPTION,
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
                    label={
                        "value": LanguageState.user_rank,
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
                    data_key="tokens_used_k",
                    name=f"{TOOLTIP_PREFIX_SECONDARY}{LanguageState.token_usage}",
                    fill=rx.color("indigo", 8),
                    bar_size=TokenAnalyzerState.user_bar_size,
                ),
                rx.recharts.bar(
                    data_key="username",
                    name=f"{TOOLTIP_PREFIX_PRIMARY}{LanguageState.user}",
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
                        "value": LanguageState.exercise_rank,
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
                    name=f"{TOOLTIP_PREFIX_PRIMARY}{LanguageState.exercise}",
                    fill="transparent",
                    bar_size=0,
                ),
                rx.recharts.bar(
                    data_key="tokens_used_k",
                    name=f"{TOOLTIP_PREFIX_SECONDARY}{LanguageState.token_usage}",
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


def token_analyzer_user_analysis_section() -> rx.Component:
    """Complete section for user-focused analysis."""
    return rx.vstack(
        token_analyzer_exercise_selector(),
        token_analyzer_bar_chart(),
        token_analyzer_table(),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
    )


def token_analyzer_exercise_analysis_section() -> rx.Component:
    """Complete section for exercise-focused analysis."""
    return rx.vstack(
        token_analyzer_user_selector(),
        token_analyzer_exercise_bar_chart(),
        token_analyzer_exercise_table(),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
    )
