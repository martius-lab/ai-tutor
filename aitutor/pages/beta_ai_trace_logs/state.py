"""State for the Beta AI trace log inspector."""

import json
import re
import unicodedata
from datetime import datetime

import reflex as rx
from pydantic import BaseModel
from reflex_local_auth.user import LocalUser
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
    return value.strftime("%d.%m.%Y, %H:%M:%S") if value else ""


def _filename_timestamp(value: datetime | None = None) -> str:
    """Return a sortable timestamp suitable for filenames."""
    return (value or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")


def _safe_filename_part(value: str | None, fallback: str = "unknown") -> str:
    """Return a lowercase, filesystem-friendly filename segment."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return (slug or fallback)[:60]


def _username_for_userinfo(session, userinfo: UserInfo | None) -> str:
    """Return the linked LocalUser username for display/export."""
    if userinfo is None:
        return "Unknown user"
    local_user = session.get(LocalUser, userinfo.user_id)
    return local_user.username if local_user else "Unknown user"


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
                        user_label=_username_for_userinfo(session, userinfo),
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
                return rx.toast.error(
                    description="Beta AI trace logs not found.",
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            beta_result = session.get(BetaExerciseResult, beta_exercise_result_id)
            if beta_result is None:
                return rx.toast.error(
                    description="Linked Beta AI exercise result not found.",
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

            export_data = self._build_trace_export_for_result(
                session=session,
                beta_result=beta_result,
                trace_logs=trace_logs,
            )
            latest_trace = export_data["latest_trace"]

            self.selected_beta_exercise_result_id = beta_exercise_result_id
            self.selected_exercise_title = export_data["exercise_title"]
            self.selected_user_label = export_data["user"]
            self.selected_conversation_json = _pretty_json(export_data["conversation"])
            self.selected_latest_trace_json = _pretty_json(latest_trace)
            self.selected_trace_history_json = _pretty_json(
                export_data["trace_history"]
            )
            self.selected_latest_turn_diagnosis_json = _pretty_json(
                latest_trace.get("latest_turn_diagnosis", {})
            )
            self.selected_cumulative_diagnosis_json = _pretty_json(
                latest_trace.get("cumulative_diagnosis", {})
            )
            self.selected_policy_basis = latest_trace.get("policy_based_on", "")

    def _build_trace_export_for_result(
        self,
        *,
        session,
        beta_result: BetaExerciseResult,
        trace_logs: list[BetaExerciseTraceLog],
    ) -> dict:
        """Build a copy/export payload for one Beta AI exercise result."""
        exercise = session.get(BetaExercise, beta_result.beta_exercise_id)
        userinfo = session.get(UserInfo, beta_result.userinfo_id)
        trace_history = [trace_log.trace_entry for trace_log in trace_logs]
        latest_trace = trace_history[-1] if trace_history else {}

        return {
            "beta_exercise_result_id": beta_result.id,
            "beta_exercise_id": beta_result.beta_exercise_id,
            "exercise_title": exercise.title if exercise else "<deleted exercise>",
            "user": _username_for_userinfo(session, userinfo),
            "conversation": beta_result.conversation_text,
            "trace_count": len(trace_logs),
            "latest_trace": latest_trace,
            "trace_history": trace_history,
        }

    def _load_trace_export_for_result(
        self, beta_exercise_result_id: int
    ) -> dict | None:
        """Load one Beta AI trace export payload by result id."""
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
            beta_result = session.get(BetaExerciseResult, beta_exercise_result_id)
            if beta_result is None or not trace_logs:
                return None
            return self._build_trace_export_for_result(
                session=session,
                beta_result=beta_result,
                trace_logs=trace_logs,
            )

    @rx.event
    def copy_trace_log(self, beta_exercise_result_id: int | None):
        """Download one exercise-result trace history as JSON."""
        if beta_exercise_result_id is None:
            return rx.toast.error(
                description="Beta AI trace log not found.",
                duration=5000,
                position="bottom-center",
                invert=True,
            )
        export_data = self._load_trace_export_for_result(beta_exercise_result_id)
        if export_data is None:
            return rx.toast.error(
                description="Beta AI trace log not found.",
                duration=5000,
                position="bottom-center",
                invert=True,
            )
        timestamp = _filename_timestamp()
        exercise_slug = _safe_filename_part(
            export_data.get("exercise_title"), "exercise"
        )
        user_slug = _safe_filename_part(export_data.get("user"), "user")
        result_id = export_data.get("beta_exercise_result_id", beta_exercise_result_id)
        return rx.download(
            data=_pretty_json(export_data),
            filename=(
                f"beta-ai-trace__{exercise_slug}__{user_slug}__"
                f"result-{result_id}__{timestamp}.json"
            ),
        )

    @rx.event
    def copy_all_trace_logs(self):
        """Download all persisted Beta AI trace histories as JSON."""
        results = []
        for row in self.trace_rows:
            export_data = self._load_trace_export_for_result(
                row.beta_exercise_result_id
            )
            if export_data is not None:
                results.append(export_data)

        exported_at = datetime.now()
        return rx.download(
            data=_pretty_json(
                {
                    "exported_at": _format_datetime(exported_at),
                    "result_count": len(results),
                    "results": results,
                }
            ),
            filename=(
                f"beta-ai-trace-logs__all-results__count-{len(results)}__"
                f"{_filename_timestamp(exported_at)}.json"
            ),
        )
