"""Tutor-only, per-message summaries of persisted Beta AI trace evaluations.

Inspired by the badge view in commit 29e555e; no imported JSON is required.
"""

from typing import Any, Literal, cast

import reflex as rx
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from aitutor.beta_ai.student_state import (
    BASIC_EVIDENCE_COMPLETENESS_THRESHOLD,
    BASIC_EVIDENCE_CORRECTNESS_THRESHOLD,
    BASIC_EVIDENCE_RELEVANCE_THRESHOLD,
    HIGHER_LEVEL_COMPLETENESS_THRESHOLD,
    HIGHER_LEVEL_CORRECTNESS_THRESHOLD,
    HIGHER_LEVEL_RELEVANCE_THRESHOLD,
    MISCONCEPTION_RESOLUTION_COMPLETENESS_THRESHOLD,
    MISCONCEPTION_RESOLUTION_CORRECTNESS_THRESHOLD,
    MISCONCEPTION_RESOLUTION_RELEVANCE_THRESHOLD,
    UNCLEAR_COMPLETENESS_THRESHOLD,
    UNCLEAR_CORRECTNESS_THRESHOLD,
    UNCLEAR_RELEVANCE_THRESHOLD,
)
from aitutor.models import BetaExerciseResult, BetaExerciseTraceLog


class EvaluationMessage(BaseModel):
    """One conversation message plus its own student-turn evaluation."""

    role: str
    content: str
    badges: list[dict[str, str]] = Field(default_factory=list)


LEVELS = {
    "basic_understanding": "Basic",
    "explain_reasoning": "Explain",
    "apply_or_compare": "Apply",
}
PATTERNS = {
    "correct_but_incomplete": "Correct, incomplete",
    "sufficient_for_completion": "Sufficient",
    "misconception_present": "Misconception",
    "shallow_keyword_only": "Too shallow",
    "off_task": "Off task",
    "unclear": "Unclear",
    "help_seeking": "Help seeking",
    "tutor_derived_answer": "Tutor-derived",
}


def _badge(label: str, color: str = "gray") -> dict[str, str]:
    return {"label": label, "color": color}


def _badges(
    trace: dict[str, Any], previous: dict[str, Any] | None
) -> list[dict[str, str]]:
    """Show the actual turn diagnosis, level transition and selected policy."""
    badges = []
    level = str(trace.get("current_question_level") or "")
    level_label = LEVELS.get(level, level.replace("_", " ").title())
    same_concept = previous is not None and previous.get("concept_label") == trace.get(
        "concept_label"
    )
    if level:
        heading = "Level: " if previous is None or same_concept else "New concept → "
        badges.append(_badge(heading + level_label, "purple"))

    diagnosis = trace.get("latest_turn_diagnosis")
    if not isinstance(diagnosis, dict):
        diagnosis = trace
    pattern = str(
        diagnosis.get("diagnosis_pattern") or trace.get("final_pattern") or ""
    )
    if pattern:
        badges.append(
            _badge(
                PATTERNS.get(pattern, pattern.replace("_", " ").title()),
                "green"
                if pattern == "sufficient_for_completion"
                else "red"
                if pattern in {"misconception_present", "off_task"}
                else "blue",
            )
        )

    if level == "basic_understanding":
        thresholds = (
            (
                MISCONCEPTION_RESOLUTION_RELEVANCE_THRESHOLD,
                MISCONCEPTION_RESOLUTION_CORRECTNESS_THRESHOLD,
                MISCONCEPTION_RESOLUTION_COMPLETENESS_THRESHOLD,
            )
            if previous and previous.get("active_misconceptions")
            else (
                BASIC_EVIDENCE_RELEVANCE_THRESHOLD,
                BASIC_EVIDENCE_CORRECTNESS_THRESHOLD,
                BASIC_EVIDENCE_COMPLETENESS_THRESHOLD,
            )
        )
    elif pattern == "unclear":
        thresholds = (
            UNCLEAR_RELEVANCE_THRESHOLD,
            UNCLEAR_CORRECTNESS_THRESHOLD,
            UNCLEAR_COMPLETENESS_THRESHOLD,
        )
    else:
        thresholds = (
            HIGHER_LEVEL_RELEVANCE_THRESHOLD,
            HIGHER_LEVEL_CORRECTNESS_THRESHOLD,
            HIGHER_LEVEL_COMPLETENESS_THRESHOLD,
        )
    status = trace.get("level_status")
    old_status = previous.get("level_status") if same_concept and previous else None
    passed = (
        isinstance(status, dict)
        and status.get(level) == "passed"
        and (not isinstance(old_status, dict) or old_status.get(level) != "passed")
    )
    for label, key, threshold in zip(
        ("Relevance", "Correctness", "Completeness"),
        ("task_relevance", "correctness", "completeness"),
        thresholds,
        strict=True,
    ):
        score = diagnosis.get(key)
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            score = max(0.0, min(1.0, float(score)))
            color = (
                "red"
                if score < threshold
                else "amber"
                if passed and score - threshold <= 0.1
                else "green"
            )
            badges.append(_badge(f"{label} {score:.0%} · min {threshold:.0%}", color))

    covered = set(trace.get("cumulative_covered_core_point_ids") or [])
    missing = set(trace.get("cumulative_missing_core_point_ids") or [])
    old_covered = (
        set(previous.get("cumulative_covered_core_point_ids") or [])
        if same_concept and previous
        else set()
    )
    if covered - old_covered:
        badges.append(
            _badge(
                f"+{len(covered - old_covered)} core points · "
                f"{len(covered)}/{len(covered | missing)} covered",
                "green",
            )
        )
    elif level == "basic_understanding" and covered | missing:
        badges.append(
            _badge(
                f"Core points {len(covered)}/{len(covered | missing)} covered",
                "red" if missing else "green",
            )
        )

    if passed:
        next_level = {
            "basic_understanding": "explain_reasoning",
            "explain_reasoning": "apply_or_compare",
        }.get(level)
        badges.append(
            _badge(
                f"{level_label} passed"
                + (f" → {LEVELS[next_level]}" if next_level else ""),
                "green",
            )
        )
    elif isinstance(status, dict) and level and status.get(level) != "passed":
        badges.append(_badge(f"{level_label} still open", "red"))
    if trace.get("misconception_flag"):
        label = str(diagnosis.get("misconception_label") or "").strip()
        badges.append(
            _badge(
                f"Misconception: {label}" if label else "Misconception detected", "red"
            )
        )
    if trace.get("selected_action"):
        action = str(trace["selected_action"]).replace("_", " ").title()
        badges.append(_badge(f"Next action: {action}", "blue"))
    return badges


def evaluated_messages(
    session: Session,
    result: BetaExerciseResult | None,
    conversation: list[dict[str, Any]],
) -> list[EvaluationMessage]:
    """Attach ordered traces only to matching answers in the visible snapshot."""
    messages = [
        EvaluationMessage(
            role=str(item.get("role", "")), content=str(item.get("content", ""))
        )
        for item in conversation
    ]
    if result is None or result.id is None:
        return messages
    traces = session.exec(
        select(BetaExerciseTraceLog)
        .where(BetaExerciseTraceLog.beta_exercise_result_id == result.id)
        .order_by(BetaExerciseTraceLog.turn_index)  # type: ignore[arg-type]
    ).all()
    student_indices = [
        i for i, message in enumerate(messages) if message.role == "student"
    ]
    previous: dict[str, Any] | None = None
    next_student = 0
    for trace in traces:
        # Some student messages never produced a trace. Match in conversation order
        # and stop once a trace's answer is absent from the visible snapshot.
        match = next(
            (
                position
                for position in range(next_student, len(student_indices))
                if messages[student_indices[position]].content == trace.student_answer
            ),
            None,
        )
        if match is None:
            break
        index = student_indices[match]
        next_student = match + 1
        entry = trace.trace_entry
        if isinstance(entry, dict):
            messages[index].badges = _badges(entry, previous)
            previous = entry
    return messages


def evaluation_badge(badge: dict[str, str]) -> rx.Component:
    """Render a compact, color-coded fact from a trace."""
    return rx.badge(
        badge["label"],
        color_scheme=cast(
            Literal["amber", "blue", "gray", "green", "orange", "purple", "red"],
            badge["color"],
        ),
        variant="soft",
        size="1",
    )


def evaluated_chat_message(message: EvaluationMessage) -> rx.Component:
    """Preserve the familiar chat bubble, adding badges under student answers."""
    from aitutor.pages.beta_ai_chat.components import chat_message

    return rx.vstack(
        chat_message({"role": message.role, "content": message.content}),
        rx.cond(
            message.role == "student",
            rx.flex(
                rx.foreach(message.badges, evaluation_badge),
                gap="0.35em",
                wrap="wrap",
                justify="end",
                width="100%",
                padding_right="0.25em",
            ),
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )
