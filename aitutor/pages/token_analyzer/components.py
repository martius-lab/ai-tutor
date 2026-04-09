"""Components for the token analyzer page."""

import reflex as rx

from aitutor.language_state import LanguageState
from aitutor.pages.token_analyzer.state import (
    EXERCISE_ANALYSIS_VIEW,
    USER_ANALYSIS_VIEW,
    ExerciseTableRow,
    TableRow,
    TokenAnalyzerState,
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
        rx.box(
            rx.text(
                label_text + ":",
                size="3",
                weight="medium",
            ),
            width="5em",
        ),
        rx.input(
            value=query_value,
            on_change=on_query_change,
            placeholder=LanguageState.starts_with_placeholder,
            width="16em",
        ),
        rx.cond(
            query_value != "",
            rx.button(
                "×",
                on_click=on_query_clear,
                variant="soft",
                size="1",
                _hover={"cursor": "pointer"},
            ),
            rx.box(width="1.625em"),
        ),
        rx.box(width="0.625em"),
        rx.select(
            items=options,
            value=selected_value,
            on_change=on_select_change,
            placeholder=placeholder,
            width="20em",
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
        options=TokenAnalyzerState.displayed_filtered_exercise_options,
        selected_value=TokenAnalyzerState.displayed_selected_exercise_name,
        on_select_change=TokenAnalyzerState.set_selected_exercise_name,
        placeholder=LanguageState.all_option,
    )


def token_analyzer_view_menu() -> rx.Component:
    """Menu to switch between user and exercise analysis views."""
    return rx.hstack(
        rx.box(
            rx.text(LanguageState.view + ":", size="3", weight="medium"),
            width="5em",
        ),
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
        options=TokenAnalyzerState.displayed_filtered_user_options,
        selected_value=TokenAnalyzerState.displayed_selected_user_name,
        on_select_change=TokenAnalyzerState.set_selected_user_name,
        placeholder=LanguageState.all_option,
    )


def token_analyzer_rank_bar_chart(
    *,
    ticks,
    rank_label,
    metadata_key: str,
    metadata_label,
    value_color,
    value_bar_size,
    chart_data,
    chart_min_width,
) -> rx.Component:
    """Shared rank-based bar chart used for token analyzer views."""
    return rx.box(
        rx.recharts.responsive_container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(
                    data_key="rank",
                    ticks=ticks,
                    interval=0,
                    label={
                        "value": rank_label,
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
                    fill=value_color,
                    bar_size=value_bar_size,
                ),
                rx.recharts.bar(
                    data_key=metadata_key,
                    name=f"{TOOLTIP_PREFIX_PRIMARY}{metadata_label}",
                    fill="transparent",
                    bar_size=0,
                ),
                data=chart_data,
                margin={"top": 30, "right": 45, "left": 6, "bottom": 24},
            ),
            width="100%",
            height=320,
            min_width=chart_min_width,
        ),
        width="85vw",
        overflow_x="auto",
    )


def token_analyzer_bar_chart() -> rx.Component:
    """Bar chart showing token usage by user rank."""
    return token_analyzer_rank_bar_chart(
        ticks=TokenAnalyzerState.chart_ticks,
        rank_label=LanguageState.user_rank,
        metadata_key="username",
        metadata_label=LanguageState.user,
        value_color=rx.color("indigo", 8),
        value_bar_size=TokenAnalyzerState.user_bar_size,
        chart_data=TokenAnalyzerState.chart_data,
        chart_min_width=TokenAnalyzerState.chart_min_width,
    )


def token_analyzer_exercise_bar_chart() -> rx.Component:
    """Bar chart showing token usage by exercise rank."""
    return token_analyzer_rank_bar_chart(
        ticks=TokenAnalyzerState.exercise_chart_ticks,
        rank_label=LanguageState.exercise_rank,
        metadata_key="exercise",
        metadata_label=LanguageState.exercise,
        value_color=rx.color("cyan", 8),
        value_bar_size=TokenAnalyzerState.exercise_bar_size,
        chart_data=TokenAnalyzerState.exercise_chart_data,
        chart_min_width=TokenAnalyzerState.exercise_chart_min_width,
    )


def token_analyzer_total_tokens_info(total_tokens) -> rx.Component:
    """Compact row showing the total token sum for the current analysis."""
    return rx.hstack(
        rx.text(LanguageState.total_tokens + ":", weight="medium"),
        rx.text(total_tokens, weight="bold"),
        align="center",
        justify="start",
        width="85vw",
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
        token_analyzer_total_tokens_info(TokenAnalyzerState.total_user_tokens),
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
        token_analyzer_total_tokens_info(TokenAnalyzerState.total_exercise_tokens),
        token_analyzer_exercise_table(),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
    )
