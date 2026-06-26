"""State for the Beta AI trace log inspector."""

import json
from datetime import datetime

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import (
    BetaExercise,
    BetaExerciseResult,
    BetaExerciseTraceLog,
    UserInfo,
    UserRole,
)


class TraceLogRow(BaseModel):
    """Simple DTO for rendering trace log rows in Reflex."""

    beta_exercise_result_id: int
    exercise_title: str
    user_label: str
    trace_count: int
    updated_at: str


def _pretty_json(value) -> str:
    """Return deterministic pretty JSON for inspector display."""
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _format_datetime(value: datetime | None) -> str:
    """Format optional datetimes for display."""
    return value.isoformat() if value else ""


class BetaAITraceLogsState(SessionState):
    """State for inspecting persisted Beta AI trace histories."""

    trace_rows: list[TraceLogRow] = []
    selected_beta_exercise_result_id: int | None = None
    selected_exercise_title: str = ""
    selected_user_label: str = ""
    selected_conversation_json: str = ""
    selected_latest_trace_json: str = ""
    selected_trace_history_json: str = ""
    selected_latest_turn_diagnosis_json: str = ""
    selected_cumulative_diagnosis_json: str = ""
    selected_policy_basis: str = ""

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialize the trace log inspector."""
        self.global_load()
        self.clear_selection()
        self.load_trace_logs()

    def on_logout(self):
        """Clear page-specific state on logout."""
        self.trace_rows = []
        self.clear_selection()

    @rx.var
    def has_selected_trace_log(self) -> bool:
        """Whether a trace log is selected for inspection."""
        return self.selected_beta_exercise_result_id is not None

    @rx.event
    def clear_selection(self):
        """Clear the selected trace log details."""
        self.selected_beta_exercise_result_id = None
        self.selected_exercise_title = ""
        self.selected_user_label = ""
        self.selected_conversation_json = ""
        self.selected_latest_trace_json = ""
        self.selected_trace_history_json = ""
        self.selected_latest_turn_diagnosis_json = ""
        self.selected_cumulative_diagnosis_json = ""
        self.selected_policy_basis = ""

    @rx.event
    def load_trace_logs(self):
        """Load trace log overview rows."""
        rows: list[TraceLogRow] = []
        with rx.session() as session:
            beta_result_ids = list(
                session.exec(
                    select(BetaExerciseTraceLog.beta_exercise_result_id).distinct()
                ).all()
            )

            for beta_result_id in beta_result_ids:
                trace_logs = list(
                    session.exec(
                        select(BetaExerciseTraceLog)
                        .where(
                            BetaExerciseTraceLog.beta_exercise_result_id
                            == beta_result_id
                        )
                        .order_by(BetaExerciseTraceLog.turn_index)  # type: ignore
                    )
                )
                if not trace_logs:
                    continue

                beta_result = session.get(BetaExerciseResult, beta_result_id)
                if beta_result is None:
                    continue
                exercise = session.get(BetaExercise, beta_result.beta_exercise_id)
                userinfo = session.get(UserInfo, beta_result.userinfo_id)
                latest_trace_log = trace_logs[-1]
                rows.append(
                    TraceLogRow(
                        beta_exercise_result_id=beta_result_id,
                        exercise_title=exercise.title
                        if exercise
                        else "<deleted exercise>",
                        user_label=(
                            f"{userinfo.email} (id={userinfo.id})"
                            if userinfo
                            else f"UserInfo id={beta_result.userinfo_id}"
                        ),
                        trace_count=len(trace_logs),
                        updated_at=_format_datetime(latest_trace_log.created_at),
                    )
                )

        self.trace_rows = sorted(rows, key=lambda row: row.updated_at, reverse=True)

    @rx.event
    def select_trace_log(self, beta_exercise_result_id: int | None):
        """Load one trace history with its linked conversation for inspection."""
        if beta_exercise_result_id is None:
            return

        with rx.session() as session:
            trace_logs = list(
                session.exec(
                    select(BetaExerciseTraceLog)
                    .where(
                        BetaExerciseTraceLog.beta_exercise_result_id
                        == beta_exercise_result_id
                    )
                    .order_by(BetaExerciseTraceLog.turn_index)  # type: ignore
                ).all()
            )
            if not trace_logs:
                return rx.toast.error("Beta AI trace logs not found.")

            beta_result = session.get(BetaExerciseResult, beta_exercise_result_id)
            if beta_result is None:
                return rx.toast.error("Linked Beta AI exercise result not found.")

            exercise = session.get(BetaExercise, beta_result.beta_exercise_id)
            userinfo = session.get(UserInfo, beta_result.userinfo_id)

            latest_trace = trace_logs[-1].trace_entry or {}
            trace_history = [trace_log.trace_entry for trace_log in trace_logs]

            self.selected_beta_exercise_result_id = beta_exercise_result_id
            self.selected_exercise_title = (
                exercise.title if exercise else "<deleted exercise>"
            )
            self.selected_user_label = (
                f"{userinfo.email} (id={userinfo.id})"
                if userinfo
                else f"UserInfo id={beta_result.userinfo_id}"
            )
            self.selected_conversation_json = _pretty_json(
                beta_result.conversation_text
            )
            self.selected_latest_trace_json = _pretty_json(latest_trace)
            self.selected_trace_history_json = _pretty_json(trace_history)
            self.selected_latest_turn_diagnosis_json = _pretty_json(
                latest_trace.get("latest_turn_diagnosis", {})
            )
            self.selected_cumulative_diagnosis_json = _pretty_json(
                latest_trace.get("cumulative_diagnosis", {})
            )
            self.selected_policy_basis = latest_trace.get("policy_based_on", "")
