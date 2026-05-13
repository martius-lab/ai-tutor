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

    trace_log_id: int
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
    selected_trace_log_id: int | None = None
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
        return self.selected_trace_log_id is not None

    @rx.event
    def clear_selection(self):
        """Clear the selected trace log details."""
        self.selected_trace_log_id = None
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
            trace_logs = list(
                session.exec(
                    select(BetaExerciseTraceLog).order_by(
                        BetaExerciseTraceLog.updated_at.desc()  # type: ignore
                    )
                ).all()
            )

            for trace_log in trace_logs:
                beta_result = session.get(
                    BetaExerciseResult, trace_log.beta_exercise_result_id
                )
                if beta_result is None:
                    continue
                exercise = session.get(BetaExercise, beta_result.beta_exercise_id)
                userinfo = session.get(UserInfo, beta_result.userinfo_id)
                rows.append(
                    TraceLogRow(
                        trace_log_id=trace_log.id or 0,
                        exercise_title=exercise.title
                        if exercise
                        else "<deleted exercise>",
                        user_label=(
                            f"{userinfo.email} (id={userinfo.id})"
                            if userinfo
                            else f"UserInfo id={beta_result.userinfo_id}"
                        ),
                        trace_count=len(trace_log.trace_history or []),
                        updated_at=_format_datetime(trace_log.updated_at),
                    )
                )

        self.trace_rows = rows

    @rx.event
    def select_trace_log(self, trace_log_id: int | None):
        """Load one trace log with its linked conversation for inspection."""
        if trace_log_id is None:
            return

        with rx.session() as session:
            trace_log = session.get(BetaExerciseTraceLog, trace_log_id)
            if trace_log is None:
                return rx.toast.error("Beta AI trace log not found.")

            beta_result = session.get(
                BetaExerciseResult, trace_log.beta_exercise_result_id
            )
            if beta_result is None:
                return rx.toast.error("Linked Beta AI exercise result not found.")

            exercise = session.get(BetaExercise, beta_result.beta_exercise_id)
            userinfo = session.get(UserInfo, beta_result.userinfo_id)

            self.selected_trace_log_id = trace_log_id
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
            self.selected_latest_trace_json = _pretty_json(trace_log.latest_trace)
            self.selected_trace_history_json = _pretty_json(trace_log.trace_history)
            latest_trace = trace_log.latest_trace or {}
            self.selected_latest_turn_diagnosis_json = _pretty_json(
                latest_trace.get("latest_turn_diagnosis", {})
            )
            self.selected_cumulative_diagnosis_json = _pretty_json(
                latest_trace.get("cumulative_diagnosis", {})
            )
            self.selected_policy_basis = latest_trace.get("policy_based_on", "")
