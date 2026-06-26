"""Components for the Beta AI trace log inspector page."""

import reflex as rx

from aitutor.pages.beta_ai_trace_logs.state import (
    BetaAITraceLogsState,
    TraceLogRow,
)


def trace_logs_header() -> rx.Component:
    """Render trace log inspector header."""
    return rx.vstack(
        rx.heading("Beta AI Trace Logs", size="7"),
        rx.text(
            "Inspect persisted Beta AI chat conversations and per-turn "
            "diagnosis/policy traces.",
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
            rx.button(
                "Inspect",
                size="2",
                on_click=BetaAITraceLogsState.select_trace_log(
                    row.beta_exercise_result_id
                ),
                _hover={"cursor": "pointer"},
            )
        ),
    )


def trace_logs_table() -> rx.Component:
    """Render trace log overview table."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Persisted Trace Logs", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh-cw"),
                    "Refresh",
                    size="2",
                    variant="soft",
                    on_click=BetaAITraceLogsState.load_trace_logs,
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
            ),
            rx.cond(
                BetaAITraceLogsState.trace_rows.length() == 0,  # type: ignore
                rx.callout(
                    "No Beta AI trace logs found yet.", icon="info", width="100%"
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Exercise"),
                            rx.table.column_header_cell("User"),
                            rx.table.column_header_cell("Trace count"),
                            rx.table.column_header_cell("Updated at"),
                            rx.table.column_header_cell("Actions"),
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
                    rx.heading("Selected Trace Log", size="4"),
                    rx.spacer(),
                    rx.button(
                        "Close",
                        size="2",
                        variant="outline",
                        on_click=BetaAITraceLogsState.clear_selection,
                        _hover={"cursor": "pointer"},
                    ),
                    width="100%",
                ),
                rx.callout(
                    "Exercise: " + BetaAITraceLogsState.selected_exercise_title,
                    icon="book-open",
                    width="100%",
                ),
                rx.callout(
                    "User: " + BetaAITraceLogsState.selected_user_label,
                    icon="user",
                    width="100%",
                ),
                rx.cond(
                    BetaAITraceLogsState.selected_policy_basis,
                    rx.callout(
                        "Policy based on: "
                        + BetaAITraceLogsState.selected_policy_basis,
                        icon="route",
                        width="100%",
                    ),
                ),
                rx.text("Conversation JSON", weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_conversation_json,
                    language="json",
                    width="100%",
                ),
                rx.text("Latest Turn Diagnosis JSON", weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_latest_turn_diagnosis_json,
                    language="json",
                    width="100%",
                ),
                rx.text("Cumulative Diagnosis Used For Policy JSON", weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_cumulative_diagnosis_json,
                    language="json",
                    width="100%",
                ),
                rx.text("Latest Trace JSON", weight="bold"),
                rx.code_block(
                    BetaAITraceLogsState.selected_latest_trace_json,
                    language="json",
                    width="100%",
                ),
                rx.text("Full Trace History JSON", weight="bold"),
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
