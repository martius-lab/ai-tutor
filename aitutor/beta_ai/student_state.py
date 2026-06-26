"""Student-state helpers for cumulative Beta AI concept evidence.

The functions in this module are part of the didactic control layer: the LLM
diagnoses one turn, but application code owns cumulative evidence, concept
state transitions, and the diagnosis view used by policy decisions.
"""

from datetime import datetime
from typing import Any, Literal

from aitutor.beta_ai.diagnosis import DiagnosisPattern, DiagnosisResponse
from aitutor.models import BetaCorePoint, BetaStudentConceptState

ConceptState = Literal[
    "unseen", "emerging", "satisfactory", "secure", "review_required"
]
QuestionLevel = Literal["basic_understanding", "explain_reasoning", "apply_or_compare"]

DEFAULT_LEVEL_STATUS = {
    "basic_understanding": "not_started",
    "explain_reasoning": "not_started",
    "apply_or_compare": "not_started",
}

MISCONCEPTION_RESOLUTION_RELEVANCE_THRESHOLD = 0.7
MISCONCEPTION_RESOLUTION_CORRECTNESS_THRESHOLD = 0.7


def normalized_level_status(level_status: dict[str, Any] | None) -> dict[str, str]:
    """Return a complete level-status dict with stable defaults."""
    normalized = dict(DEFAULT_LEVEL_STATUS)
    for key, value in dict(level_status or {}).items():
        if key in normalized and value in {"not_started", "in_progress", "passed"}:
            normalized[key] = str(value)
    return normalized


def valid_core_point_ids(core_points: list[BetaCorePoint]) -> list[int]:
    """Return known persisted core-point IDs in deterministic order."""
    return sorted(core_point.id for core_point in core_points if core_point.id)


def required_core_point_ids(core_points: list[BetaCorePoint]) -> list[int]:
    """Return required persisted core-point IDs in deterministic order.

    This is the completion criterion for the Beta AI Tutor: a concept can only
    be considered sufficiently covered when all instructor-curated required core
    points have cumulative student-owned evidence. This replaces the earlier
    prototype heuristic that used an arbitrary 80% coverage threshold.
    """
    return sorted(
        core_point.id
        for core_point in core_points
        if core_point.id and core_point.required
    )


def build_cumulative_evidence_summary(
    *,
    core_points: list[BetaCorePoint],
    covered_core_point_ids: list[int],
    missing_core_point_ids: list[int],
) -> str:
    """Build a compact prompt summary of cumulative concept evidence so far."""
    core_points_by_id = {
        core_point.id: core_point for core_point in core_points if core_point.id
    }

    covered_lines = [
        f"- {core_point_id}: {core_points_by_id[core_point_id].text}"
        for core_point_id in covered_core_point_ids
        if core_point_id in core_points_by_id
    ]
    missing_lines = [
        f"- {core_point_id}: {core_points_by_id[core_point_id].text}"
        for core_point_id in missing_core_point_ids
        if core_point_id in core_points_by_id
    ]

    return (
        "Covered core points so far:\n"
        f"{chr(10).join(covered_lines) if covered_lines else '- None yet.'}\n\n"
        "Still missing core points:\n"
        f"{chr(10).join(missing_lines) if missing_lines else '- None.'}"
    )


def _normalize_misconception_label(label: str) -> str:
    """Return a stable key for matching repeated misconception labels."""
    normalized = " ".join(label.lower().split())
    return normalized.strip(" .!?:;\"'")


def _fallback_misconception_label(latest_diagnosis: DiagnosisResponse) -> str:
    """Return a safe label when the diagnosis did not provide one."""
    if latest_diagnosis.misconception_label.strip():
        return latest_diagnosis.misconception_label.strip()
    if latest_diagnosis.evidence_snippets:
        return latest_diagnosis.evidence_snippets[0].strip()[:120]
    return "Unspecified misconception"


def _is_misconception_resolution_answer(
    latest_diagnosis: DiagnosisResponse,
) -> bool:
    """Return whether this answer can resolve active misconceptions."""
    return (
        latest_diagnosis.is_answer_attempt
        and latest_diagnosis.is_student_owned_evidence
        and not latest_diagnosis.misconception_flag
        and latest_diagnosis.diagnosis_pattern
        not in {
            "help_seeking",
            "tutor_derived_answer",
            "off_task",
            "shallow_keyword_only",
            "misconception_present",
        }
        and latest_diagnosis.task_relevance
        >= MISCONCEPTION_RESOLUTION_RELEVANCE_THRESHOLD
        and latest_diagnosis.correctness
        >= MISCONCEPTION_RESOLUTION_CORRECTNESS_THRESHOLD
    )


def update_misconception_memory(
    *,
    student_state: BetaStudentConceptState,
    latest_diagnosis: DiagnosisResponse,
    student_answer: str,
    trace_reference: int,
    now: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Update active/resolved misconception memory for one turn.

    Returns active misconceptions, resolved misconceptions, and whether active
    misconceptions were resolved by this answer.
    """
    active = [dict(item) for item in student_state.active_misconceptions or []]
    resolved = [dict(item) for item in student_state.resolved_misconceptions or []]

    if latest_diagnosis.misconception_flag:
        label = _fallback_misconception_label(latest_diagnosis)
        key = _normalize_misconception_label(label)
        matching_entry = next(
            (
                entry
                for entry in active
                if entry.get("key") == key
                or _normalize_misconception_label(str(entry.get("label", ""))) == key
            ),
            None,
        )
        if matching_entry is None:
            active.append(
                {
                    "key": key,
                    "label": label,
                    "status": "active",
                    "first_seen_turn": trace_reference,
                    "last_seen_turn": trace_reference,
                    "hit_count": 1,
                    "evidence_snippets": latest_diagnosis.evidence_snippets,
                    "last_student_answer": student_answer,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            )
        else:
            matching_entry["last_seen_turn"] = trace_reference
            matching_entry["hit_count"] = int(matching_entry.get("hit_count", 0)) + 1
            matching_entry["evidence_snippets"] = latest_diagnosis.evidence_snippets
            matching_entry["last_student_answer"] = student_answer
            matching_entry["updated_at"] = now.isoformat()
        return active, resolved, False

    if active and _is_misconception_resolution_answer(latest_diagnosis):
        for entry in active:
            resolved_entry = dict(entry)
            resolved_entry["status"] = "resolved"
            resolved_entry["resolved_at_turn"] = trace_reference
            resolved_entry["resolution_evidence_snippets"] = (
                latest_diagnosis.evidence_snippets
            )
            resolved_entry["resolution_student_answer"] = student_answer
            resolved_entry["resolved_at"] = now.isoformat()
            resolved.append(resolved_entry)
        return [], resolved, True

    return active, resolved, False


def derive_cumulative_pattern(
    *,
    latest_diagnosis: DiagnosisResponse,
    cumulative_covered_ids: list[int],
    all_core_point_ids: list[int],
    required_core_point_ids: list[int],
    student_answer: str,
) -> DiagnosisPattern:
    """Derive the policy-facing pattern from cumulative concept evidence.

    This is intentionally separate from the per-turn diagnosis pattern. The LLM
    and validator classify what the current answer shows; this function asks what
    the tutor should conclude after merging evidence across all turns for the
    current concept.
    """
    if (
        not latest_diagnosis.is_answer_attempt
        or latest_diagnosis.diagnosis_pattern == "help_seeking"
    ):
        return "help_seeking"
    if (
        not latest_diagnosis.is_student_owned_evidence
        or latest_diagnosis.diagnosis_pattern == "tutor_derived_answer"
    ):
        return "tutor_derived_answer"
    if latest_diagnosis.diagnosis_pattern == "shallow_keyword_only":
        return "shallow_keyword_only"

    all_required_covered = bool(required_core_point_ids) and set(
        required_core_point_ids
    ).issubset(set(cumulative_covered_ids))

    if not student_answer.strip() or (
        latest_diagnosis.task_relevance < 0.3 and not cumulative_covered_ids
    ):
        return "off_task"
    if latest_diagnosis.misconception_flag:
        return "misconception_present"
    if all_required_covered and latest_diagnosis.task_relevance >= 0.5:
        return "sufficient_for_completion"
    if cumulative_covered_ids and latest_diagnosis.task_relevance >= 0.3:
        return "correct_but_incomplete"
    return "unclear"


def is_level_successful_answer(
    latest_diagnosis: DiagnosisResponse,
    question_level: QuestionLevel,
) -> bool:
    """Return whether the latest turn is sufficient evidence for its level.

    Basic understanding is still governed by cumulative required core-point
    coverage in ``update_student_concept_state_from_diagnosis``. Higher levels
    are concept-level checks: one relevant, correct, student-owned explanation
    or application answer can pass the level without re-covering every core
    point in the current turn.
    """
    if not latest_diagnosis.is_answer_attempt:
        return False
    if not latest_diagnosis.is_student_owned_evidence:
        return False
    if latest_diagnosis.misconception_flag:
        return False

    if question_level == "basic_understanding":
        return latest_diagnosis.diagnosis_pattern == "sufficient_for_completion"

    if latest_diagnosis.diagnosis_pattern in {
        "help_seeking",
        "tutor_derived_answer",
        "off_task",
        "shallow_keyword_only",
        "misconception_present",
    }:
        return False

    threshold = 0.85 if latest_diagnosis.diagnosis_pattern == "unclear" else 0.7
    return (
        latest_diagnosis.task_relevance >= threshold
        and latest_diagnosis.correctness >= threshold
    )


def update_student_concept_state_from_diagnosis(
    *,
    student_state: BetaStudentConceptState,
    latest_diagnosis: DiagnosisResponse,
    core_points: list[BetaCorePoint],
    student_answer: str,
    trace_reference: int,
    now: datetime,
    question_level: QuestionLevel = "basic_understanding",
) -> DiagnosisResponse:
    """Update persisted student concept state and return the cumulative diagnosis.

    The latest diagnosis remains a per-turn observation. This function merges that
    observation into persisted cumulative evidence and returns a policy-facing view
    over all evidence collected for the current student/concept so far.
    """
    all_core_point_ids = valid_core_point_ids(core_points)
    required_ids = required_core_point_ids(core_points)
    all_core_point_id_set = set(all_core_point_ids)
    is_evidence_eligible = (
        latest_diagnosis.is_answer_attempt
        and latest_diagnosis.is_student_owned_evidence
        and latest_diagnosis.diagnosis_pattern
        in {
            "correct_but_incomplete",
            "sufficient_for_completion",
        }
    )

    previous_covered_ids = set(student_state.covered_core_point_ids or [])
    latest_covered_ids = (
        set(latest_diagnosis.covered_core_point_ids) if is_evidence_eligible else set()
    )
    cumulative_covered_ids = sorted(
        (previous_covered_ids | latest_covered_ids) & all_core_point_id_set
    )
    cumulative_missing_ids = sorted(all_core_point_id_set - set(cumulative_covered_ids))

    evidence_by_core_point: dict[str, Any] = dict(
        student_state.evidence_by_core_point or {}
    )
    for core_point_id in latest_covered_ids:
        if core_point_id not in all_core_point_id_set:
            continue
        key = str(core_point_id)
        entries = list(evidence_by_core_point.get(key, []))
        entries.append(
            {
                "turn_index": trace_reference,
                "student_answer": student_answer,
                "evidence_snippets": latest_diagnosis.evidence_snippets,
                "diagnosis_pattern": latest_diagnosis.diagnosis_pattern,
                "created_at": now.isoformat(),
            }
        )
        evidence_by_core_point[key] = entries

    cumulative_pattern = derive_cumulative_pattern(
        latest_diagnosis=latest_diagnosis,
        cumulative_covered_ids=cumulative_covered_ids,
        all_core_point_ids=all_core_point_ids,
        required_core_point_ids=required_ids,
        student_answer=student_answer,
    )
    coverage_ratio = (
        len(cumulative_covered_ids) / len(all_core_point_ids)
        if all_core_point_ids
        else 0.0
    )
    all_required_covered = set(required_ids).issubset(set(cumulative_covered_ids))
    active_misconceptions, resolved_misconceptions, resolved_this_turn = (
        update_misconception_memory(
            student_state=student_state,
            latest_diagnosis=latest_diagnosis,
            student_answer=student_answer,
            trace_reference=trace_reference,
            now=now,
        )
    )
    has_active_misconception = bool(active_misconceptions)
    latest_turn_sufficient_success = is_level_successful_answer(
        latest_diagnosis, question_level
    )

    level_status = normalized_level_status(student_state.level_status)
    level_evidence: dict[str, Any] = dict(student_state.level_evidence or {})

    if question_level in level_status and level_status[question_level] == "not_started":
        level_status[question_level] = "in_progress"

    if all_required_covered and not has_active_misconception:
        level_status["basic_understanding"] = "passed"
        level_evidence["basic_understanding"] = {
            "passed_at_turn": trace_reference,
            "covered_required_core_point_ids": required_ids,
        }

    if (
        question_level == "explain_reasoning"
        and latest_turn_sufficient_success
        and level_status["basic_understanding"] == "passed"
        and not has_active_misconception
    ):
        level_status["explain_reasoning"] = "passed"
        level_evidence["explain_reasoning"] = {
            "passed_at_turn": trace_reference,
            "evidence_snippets": latest_diagnosis.evidence_snippets,
        }

    if (
        question_level == "apply_or_compare"
        and latest_turn_sufficient_success
        and level_status["explain_reasoning"] == "passed"
        and not has_active_misconception
    ):
        level_status["apply_or_compare"] = "passed"
        level_evidence["apply_or_compare"] = {
            "passed_at_turn": trace_reference,
            "evidence_snippets": latest_diagnosis.evidence_snippets,
        }

    student_state.attempts_total += 1
    student_state.covered_core_point_ids = cumulative_covered_ids
    student_state.missing_core_point_ids = cumulative_missing_ids
    student_state.evidence_by_core_point = evidence_by_core_point
    student_state.level_status = level_status
    student_state.level_evidence = level_evidence
    student_state.active_misconceptions = active_misconceptions
    student_state.resolved_misconceptions = resolved_misconceptions
    student_state.last_diagnosis_pattern = latest_diagnosis.diagnosis_pattern
    student_state.updated_at = now

    if level_status["apply_or_compare"] == "passed":
        student_state.state = "secure"
    elif (
        level_status["basic_understanding"] == "passed"
        and level_status["explain_reasoning"] == "passed"
    ):
        student_state.state = "satisfactory"
    elif cumulative_pattern == "sufficient_for_completion":
        student_state.successful_attempts += 1
        if student_state.state == "unseen":
            student_state.state = "emerging"
    elif cumulative_pattern == "misconception_present":
        student_state.misconception_hits += 1
        # Misconceptions are handled by the tutor's automatic repair loop
        # (contrast question / targeted misconception repair). They should be
        # logged for diagnostics, but they should not move the concept into a
        # human-review terminal state: the Beta AI design goal is that the tutor
        # pauses normal progression and keeps repairing until the current answer
        # no longer contains the misconception.
        if student_state.state not in {"satisfactory", "secure"}:
            student_state.state = "emerging"
    elif cumulative_pattern == "correct_but_incomplete":
        if student_state.state == "unseen" or student_state.state not in {
            "satisfactory",
            "secure",
        }:
            student_state.state = "emerging"
    elif (
        cumulative_pattern
        in {
            "off_task",
            "unclear",
            "help_seeking",
            "shallow_keyword_only",
            "tutor_derived_answer",
        }
        and student_state.state == "unseen"
    ):
        student_state.state = "emerging"

    policy_pattern = cumulative_pattern
    if question_level in {
        "explain_reasoning",
        "apply_or_compare",
    } and latest_diagnosis.diagnosis_pattern in {
        "correct_but_incomplete",
        "help_seeking",
        "tutor_derived_answer",
        "shallow_keyword_only",
        "misconception_present",
        "off_task",
        "unclear",
    }:
        # For higher-level questions, current non-evidence or problematic turns
        # should influence the policy pattern, but must not erase cumulative
        # concept coverage collected in earlier student-owned turns.
        policy_pattern = latest_diagnosis.diagnosis_pattern

    return DiagnosisResponse(
        student_intent=latest_diagnosis.student_intent,
        is_answer_attempt=latest_diagnosis.is_answer_attempt,
        evidence_origin=latest_diagnosis.evidence_origin,
        is_student_owned_evidence=latest_diagnosis.is_student_owned_evidence,
        task_relevance=latest_diagnosis.task_relevance,
        correctness=latest_diagnosis.correctness,
        completeness=coverage_ratio,
        misconception_flag=latest_diagnosis.misconception_flag,
        misconception_label=latest_diagnosis.misconception_label,
        diagnosis_pattern=policy_pattern,
        covered_core_point_ids=cumulative_covered_ids,
        missing_core_point_ids=cumulative_missing_ids,
        evidence_snippets=latest_diagnosis.evidence_snippets,
        explanation=(
            latest_diagnosis.explanation
            + "\n\nCumulative view: policy is based on all core points covered "
            "across this concept's chat turns."
            + (
                " Active misconceptions were resolved by this answer."
                if resolved_this_turn
                else ""
            )
        ),
    )
