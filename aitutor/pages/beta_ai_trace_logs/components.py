"""Components for the Beta AI trace log inspector page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.beta_ai_trace_logs.state import (
    BetaAITraceLogsState,
    TraceLogRow,
)


def trace_logs_header() -> rx.Component:
    """Render trace log inspector header."""
    return rx.vstack(
        rx.heading(LS.beta_ai_trace_logs, size="7"),
        rx.text(
            LS.beta_ai_trace_logs_subtitle,
            color_scheme="gray",
        ),
        align="start",
        spacing="1",
        width="100%",
    )


def trace_log_row(row: TraceLogRow) -> rx.Component:
    """Render one trace log overview row."""
    return rx.table.row(
        rx.table.cell(row.exercise_title),
        rx.table.cell(row.user_label),
        rx.table.cell(row.trace_count),
        rx.table.cell(row.updated_at),
        rx.table.cell(
            rx.hstack(
                rx.icon_button(
                    rx.icon("download", size=16),
                    size="2",
                    variant="soft",
                    on_click=BetaAITraceLogsState.copy_trace_log(
                        row.beta_exercise_result_id
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    LS.beta_ai_inspect,
                    size="2",
                    on_click=BetaAITraceLogsState.select_trace_log(
                        row.beta_exercise_result_id
                    ),
                    _hover={"cursor": "pointer"},
                ),
                spacing="2",
            )
        ),
    )


def trace_logs_table() -> rx.Component:
    """Render trace log overview table."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(LS.beta_ai_persisted_trace_logs, size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("download"),
                    LS.beta_ai_download_all,
                    size="2",
                    variant="soft",
                    on_click=BetaAITraceLogsState.copy_all_trace_logs,
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
            ),
            rx.cond(
                BetaAITraceLogsState.trace_rows.length() == 0,  # type: ignore
                rx.callout(LS.beta_ai_no_trace_logs, icon="info", width="100%"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(LS.exercise),
                            rx.table.column_header_cell(LS.user),
                            rx.table.column_header_cell(LS.beta_ai_trace_count),
                            rx.table.column_header_cell(LS.beta_ai_updated_at),
                            rx.table.column_header_cell(LS.beta_ai_actions),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(BetaAITraceLogsState.trace_rows, trace_log_row)
                    ),
                    variant="surface",
                    width="100%",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def selected_trace_log_details() -> rx.Component:
    """Render selected trace log detail inspector."""
    return rx.cond(
        BetaAITraceLogsState.has_selected_trace_log,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(LS.beta_ai_selected_trace_log, size="4"),
                    rx.spacer(),
                    rx.button(
                        LS.close,
                        size="2",
                        variant="outline",
                        on_click=BetaAITraceLogsState.clear_selection,
                        _hover={"cursor": "pointer"},
                    ),
                    width="100%",
                ),
                rx.callout(
                    LS.exercise + ": " + BetaAITraceLogsState.selected_exercise_title,
                    icon="book-open",
                    width="100%",
                ),
                rx.callout(
                    LS.user + ": " + BetaAITraceLogsState.selected_user_label,
                    icon="user",
                    width="100%",
                ),
                rx.cond(
                    BetaAITraceLogsState.selected_policy_basis,
                    rx.callout(
                        LS.beta_ai_policy_based_on
                        + BetaAITraceLogsState.selected_policy_basis,
                        icon="route",
                        width="100%",
                    ),
                ),
                rx.text(LS.beta_ai_conversation_json, weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_conversation_json,
                    language="json",
                    width="100%",
                ),
                rx.text(LS.beta_ai_latest_turn_diagnosis_json, weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_latest_turn_diagnosis_json,
                    language="json",
                    width="100%",
                ),
                rx.text(LS.beta_ai_cumulative_diagnosis_json, weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_cumulative_diagnosis_json,
                    language="json",
                    width="100%",
                ),
                rx.text(LS.beta_ai_latest_trace_json, weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_latest_trace_json,
                    language="json",
                    width="100%",
                ),
                rx.text(LS.beta_ai_full_trace_history_json, weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_trace_history_json,
                    language="json",
                    width="100%",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            width="100%",
        ),
    )


def beta_ai_trace_logs_content() -> rx.Component:
    """Render full Beta AI trace log inspector content."""
    return rx.vstack(
        trace_logs_header(),
        trace_logs_table(),
        selected_trace_log_details(),
        spacing="4",
        width="100%",
    )
