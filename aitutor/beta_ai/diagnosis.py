"""Diagnosis schemas and helpers for the Beta AI Tutor."""

from difflib import SequenceMatcher
from typing import Literal, cast

import decouple
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from aitutor.config import get_config
from aitutor.models import BetaCorePoint, BetaMisconception

DiagnosisPattern = Literal[
    "off_task",
    "help_seeking",
    "tutor_derived_answer",
    "correct_but_incomplete",
    "misconception_present",
    "sufficient_for_completion",
    "shallow_keyword_only",
    "unclear",
]

StudentIntent = Literal[
    "answer_attempt",
    "hint_request",
    "answer_request",
    "example_request",
    "clarification_request",
    "meta_chat",
    "off_task",
]

EvidenceOrigin = Literal[
    "student_generated",
    "tutor_derived",
    "copied_from_tutor",
    "unclear",
]


class DiagnosisResponse(BaseModel):
    """Structured diagnosis result for one student answer."""

    student_intent: StudentIntent = "answer_attempt"
    is_answer_attempt: bool = True
    evidence_origin: EvidenceOrigin = "student_generated"
    is_student_owned_evidence: bool = True
    task_relevance: float = 0.0
    correctness: float = 0.0
    completeness: float = 0.0
    misconception_flag: bool = False
    diagnosis_pattern: DiagnosisPattern = "unclear"
    covered_core_point_ids: list[int] = Field(default_factory=list)
    missing_core_point_ids: list[int] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    explanation: str = ""


class DiagnosisValidationResult(BaseModel):
    """Result of validating and normalizing an LLM diagnosis."""

    diagnosis: DiagnosisResponse
    llm_suggested_pattern: DiagnosisPattern
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _format_core_points(core_points: list[BetaCorePoint]) -> str:
    """Format persisted core points for the diagnosis prompt."""
    formatted_points = []
    for core_point in core_points:
        if core_point.id is None:
            continue
        formatted_points.append(f"- {core_point.id}: {core_point.text}")
    return "\n".join(formatted_points) or "No core points provided."


def _format_misconceptions(misconceptions: list[BetaMisconception]) -> str:
    """Format persisted misconception hints for the diagnosis prompt."""
    formatted_misconceptions = []
    for misconception in misconceptions:
        description = (
            f" — {misconception.description}" if misconception.description else ""
        )
        formatted_misconceptions.append(f"- {misconception.label}{description}")
    return "\n".join(formatted_misconceptions) or "No known misconceptions provided."


def _format_conversation_context(
    conversation_context: list[dict[str, str]] | None,
) -> str:
    """Format prior chat messages for the diagnosis prompt."""
    if not conversation_context:
        return "No prior conversation context provided."

    formatted_messages = []
    for message in conversation_context:
        role = message.get("role", "unknown")
        content = " ".join(message.get("content", "").split())
        if not content:
            continue
        display_role = "Student" if role == "student" else "Tutor"
        formatted_messages.append(f"{display_role}: {content}")

    return "\n".join(formatted_messages) or "No prior conversation context provided."


def _format_cumulative_evidence_summary(cumulative_evidence_summary: str | None) -> str:
    """Format the optional cumulative concept evidence summary for the prompt."""
    if not cumulative_evidence_summary or not cumulative_evidence_summary.strip():
        return "No cumulative concept evidence has been recorded yet."
    return cumulative_evidence_summary.strip()


def _clamp_score(value: float) -> float:
    """Clamp a diagnosis score to the valid 0.0-1.0 range."""
    return max(0.0, min(1.0, value))


def _required_core_point_ids(core_points: list[BetaCorePoint]) -> set[int]:
    """Return required core-point IDs used for transparent completion checks.

    Completion should not depend on an arbitrary percentage threshold. It should
    require the instructor-curated required core points. In the current builder,
    core points are required by default, so this behaves like a strict 100%
    required-coverage rule unless optional core points are introduced later.
    """
    return {
        core_point.id
        for core_point in core_points
        if core_point.id and core_point.required
    }


def detect_non_answer_intent(student_answer: str) -> StudentIntent | None:
    """Detect obvious help/answer/example requests before evidence is accepted."""
    normalized = " ".join(student_answer.lower().split())
    if not normalized:
        return None

    answer_markers = [
        "give me the answer",
        "show me the answer",
        "tell me the answer",
        "what is the answer",
        "solve it for me",
        "sag mir die antwort",
        "gib mir die antwort",
        "gib mir die lösung",
        "loesung",
        "lösung",
    ]
    hint_markers = [
        "give me a hint",
        "can you give me a hint",
        "hint please",
        "give hint",
        "gib mir einen hint",
        "gib mir ein hinweis",
        "hinweis bitte",
    ]
    example_markers = [
        "give me an example",
        "show me an example",
        "can you give me an example",
        "for example?",
        "gib mir ein beispiel",
        "zeig mir ein beispiel",
    ]
    clarification_markers = [
        "i don't understand the question",
        "i do not understand the question",
        "what do you mean",
        "was meinst du",
        "ich verstehe die frage nicht",
    ]

    if any(marker in normalized for marker in answer_markers):
        return "answer_request"
    if any(marker in normalized for marker in hint_markers):
        return "hint_request"
    if any(marker in normalized for marker in example_markers):
        return "example_request"
    if any(marker in normalized for marker in clarification_markers):
        return "clarification_request"
    return None


def _normalize_for_similarity(value: str) -> str:
    """Normalize text for coarse copy/paste similarity checks."""
    return " ".join(value.lower().split())


def detect_copied_from_tutor(
    *,
    student_answer: str,
    conversation_context: list[dict[str, str]] | None,
    similarity_threshold: float = 0.82,
) -> bool:
    """Detect whether the student answer is likely copied from recent tutor text."""
    normalized_answer = _normalize_for_similarity(student_answer)
    if len(normalized_answer) < 24 or not conversation_context:
        return False

    for message in reversed(conversation_context[-8:]):
        if message.get("role") != "tutor":
            continue
        tutor_text = _normalize_for_similarity(message.get("content", ""))
        if len(tutor_text) < 24:
            continue
        if normalized_answer in tutor_text:
            return True
        if (
            SequenceMatcher(None, normalized_answer, tutor_text).ratio()
            >= similarity_threshold
        ):
            return True
    return False


def validate_and_normalize_diagnosis(
    diagnosis: DiagnosisResponse,
    *,
    core_points: list[BetaCorePoint],
    student_answer: str,
    conversation_context: list[dict[str, str]] | None = None,
) -> DiagnosisValidationResult:
    """
    Validate LLM output and derive the final didactic pattern from core-point evidence.

    The LLM may propose a diagnosis pattern, but the app controls the final
    pattern using constrained, auditable rules over task relevance,
    misconception flag, and covered vs. missing core points.
    """
    errors: list[str] = []
    warnings: list[str] = []
    llm_suggested_pattern = diagnosis.diagnosis_pattern
    answer_word_count = len(student_answer.split())
    detected_intent = detect_non_answer_intent(student_answer)
    copied_from_tutor = detect_copied_from_tutor(
        student_answer=student_answer,
        conversation_context=conversation_context,
    )
    student_intent = detected_intent or diagnosis.student_intent
    evidence_origin = (
        "copied_from_tutor" if copied_from_tutor else diagnosis.evidence_origin
    )
    is_student_owned_evidence = (
        diagnosis.is_student_owned_evidence
        and evidence_origin not in {"copied_from_tutor", "tutor_derived"}
    )
    is_answer_attempt = (
        diagnosis.is_answer_attempt and student_intent == "answer_attempt"
    )

    valid_core_point_ids = {
        core_point.id for core_point in core_points if core_point.id
    }
    covered_ids = set(diagnosis.covered_core_point_ids)
    missing_ids = set(diagnosis.missing_core_point_ids)

    invalid_covered_ids = sorted(covered_ids - valid_core_point_ids)
    invalid_missing_ids = sorted(missing_ids - valid_core_point_ids)
    if invalid_covered_ids:
        errors.append(f"Invalid covered core point IDs removed: {invalid_covered_ids}")
    if invalid_missing_ids:
        errors.append(f"Invalid missing core point IDs removed: {invalid_missing_ids}")

    covered_ids &= valid_core_point_ids
    missing_ids &= valid_core_point_ids

    overlapping_ids = sorted(covered_ids & missing_ids)
    if overlapping_ids:
        warnings.append(
            "Core point IDs appeared as both covered and missing; keeping as "
            f"covered: {overlapping_ids}"
        )
        missing_ids -= covered_ids

    missing_ids |= valid_core_point_ids - covered_ids - missing_ids

    normalized_evidence = []
    lower_student_answer = student_answer.lower()
    for snippet in diagnosis.evidence_snippets:
        stripped_snippet = snippet.strip()
        if not stripped_snippet:
            continue
        if stripped_snippet.lower() not in lower_student_answer:
            warnings.append(
                "Evidence snippet is not a verbatim part of the student "
                f"answer and was removed: {stripped_snippet}"
            )
            continue
        normalized_evidence.append(stripped_snippet)

    normalized = DiagnosisResponse(
        student_intent=student_intent,
        is_answer_attempt=is_answer_attempt,
        evidence_origin=evidence_origin,  # type: ignore[arg-type]
        is_student_owned_evidence=is_student_owned_evidence,
        task_relevance=_clamp_score(diagnosis.task_relevance),
        correctness=_clamp_score(diagnosis.correctness),
        completeness=_clamp_score(diagnosis.completeness),
        misconception_flag=diagnosis.misconception_flag,
        diagnosis_pattern=diagnosis.diagnosis_pattern,
        covered_core_point_ids=sorted(covered_ids),
        missing_core_point_ids=sorted(missing_ids),
        evidence_snippets=normalized_evidence,
        explanation=diagnosis.explanation,
    )

    if not normalized.is_answer_attempt:
        warnings.append(
            f"Student intent '{normalized.student_intent}' is not answer "
            "evidence; coverage removed."
        )
        normalized.covered_core_point_ids = []
        normalized.missing_core_point_ids = sorted(valid_core_point_ids)
        normalized.completeness = 0.0

    if not normalized.is_student_owned_evidence:
        warnings.append(
            f"Evidence origin '{normalized.evidence_origin}' is not "
            "student-owned; coverage removed."
        )
        normalized.covered_core_point_ids = []
        normalized.missing_core_point_ids = sorted(valid_core_point_ids)
        normalized.completeness = 0.0

    if (
        normalized.is_answer_attempt
        and answer_word_count < 4
        and normalized.covered_core_point_ids
    ):
        warnings.append(
            "Keyword-only or very short answer rejected as insufficient "
            "conceptual evidence."
        )
        normalized.covered_core_point_ids = []
        normalized.missing_core_point_ids = sorted(valid_core_point_ids)
        normalized.completeness = 0.0

    if normalized.task_relevance != diagnosis.task_relevance:
        warnings.append("Task relevance score was clamped to the 0.0-1.0 range.")
    if normalized.correctness != diagnosis.correctness:
        warnings.append("Correctness score was clamped to the 0.0-1.0 range.")
    if normalized.completeness != diagnosis.completeness:
        warnings.append("Completeness score was clamped to the 0.0-1.0 range.")

    covered_count = len(normalized.covered_core_point_ids)
    required_ids = _required_core_point_ids(core_points)
    all_required_covered = bool(required_ids) and required_ids.issubset(
        set(normalized.covered_core_point_ids)
    )

    if not normalized.is_answer_attempt:
        final_pattern: DiagnosisPattern = "help_seeking"
    elif not normalized.is_student_owned_evidence:
        final_pattern = "tutor_derived_answer"
    elif (
        answer_word_count < 4
        and normalized.task_relevance >= 0.3
        and student_answer.strip()
    ):
        final_pattern: DiagnosisPattern = "shallow_keyword_only"
    elif not student_answer.strip() or (
        normalized.task_relevance < 0.3 and covered_count == 0
    ):
        final_pattern = "off_task"
    elif normalized.misconception_flag:
        final_pattern = "misconception_present"
    elif all_required_covered and normalized.task_relevance >= 0.5:
        final_pattern = "sufficient_for_completion"
    elif covered_count > 0 and normalized.task_relevance >= 0.3:
        final_pattern = "correct_but_incomplete"
    else:
        final_pattern = "unclear"

    if final_pattern != llm_suggested_pattern:
        warnings.append(
            f"LLM suggested '{llm_suggested_pattern}', app normalized to "
            f"'{final_pattern}'."
        )

    normalized.diagnosis_pattern = final_pattern

    return DiagnosisValidationResult(
        diagnosis=normalized,
        llm_suggested_pattern=llm_suggested_pattern,
        errors=errors,
        warnings=warnings,
    )


async def run_llm_diagnosis(
    *,
    exercise_title: str,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    misconceptions: list[BetaMisconception],
    student_answer: str,
    conversation_context: list[dict[str, str]] | None = None,
    cumulative_evidence_summary: str | None = None,
    current_question: str = "",
    current_question_level: str = "basic_understanding",
    current_focus_core_point_id: int | None = None,
) -> DiagnosisResponse:
    """Run a structured LLM diagnosis for one answer against concept core points."""
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    core_point_ids = [core_point.id for core_point in core_points if core_point.id]
    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a diagnostic component for a university AI tutor. "
                    "Evaluate the student's answer only against the provided concept, "
                    "core points, and known misconceptions. Return only "
                    "structured data matching the required schema. Use scores "
                    "from 0.0 to 1.0. Select "
                    "exactly one diagnosis_pattern. Only use core point IDs that are "
                    "explicitly listed in the prompt. Evidence snippets must be short "
                    "verbatim excerpts from the student answer. Do not use outside "
                    "knowledge or the original teaching material. Conversation history "
                    "and cumulative evidence may be used only to interpret references "
                    "and the tutoring focus. Diagnose the current student answer, not "
                    "the entire conversation. "
                    "Do not mark a core point covered solely because it "
                    "appeared earlier "
                    "unless the current answer clearly refers back to it. Do not grant "
                    "coverage for keyword-only answers or copied isolated "
                    "phrases. Coverage requires a meaningful explanation, "
                    "relation, function, condition, or example. "
                    "First classify student_intent. If the student asks for "
                    "a hint, example, "
                    "answer, solution, clarification, or asks you to solve it, set "
                    "is_answer_attempt=false, diagnosis_pattern='help_seeking', "
                    "and covered_core_point_ids=[]. "
                    "Also compare the student answer with prior Tutor messages. "
                    "If the answer "
                    "mostly repeats wording or examples provided by the Tutor, set "
                    "evidence_origin='copied_from_tutor' or 'tutor_derived', "
                    "is_student_owned_evidence=false, "
                    "diagnosis_pattern='tutor_derived_answer', "
                    "and covered_core_point_ids=[]."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Exercise title: {exercise_title}\n\n"
                    f"Concept: {concept_label}\n"
                    f"Concept description: {concept_description}\n\n"
                    "Core points with allowed IDs:\n"
                    f"{_format_core_points(core_points)}\n\n"
                    f"Allowed core point IDs: {core_point_ids}\n\n"
                    "Known misconceptions:\n"
                    f"{_format_misconceptions(misconceptions)}\n\n"
                    "Conversation context:\n"
                    f"{_format_conversation_context(conversation_context)}\n\n"
                    "Cumulative concept evidence so far:\n"
                    f"{_format_cumulative_evidence_summary(cumulative_evidence_summary)}\n\n"
                    "Current tutor question context:\n"
                    "Question: "
                    f"{current_question or 'No previous tutor question yet.'}\n"
                    f"Question level: {current_question_level}\n"
                    f"Focus core point ID: {current_focus_core_point_id}\n\n"
                    "Student answer:\n"
                    f"{student_answer}\n\n"
                    "Required JSON fields: student_intent, is_answer_attempt, "
                    "evidence_origin, is_student_owned_evidence, "
                    "task_relevance, correctness, completeness, "
                    "misconception_flag, diagnosis_pattern, covered_core_point_ids, "
                    "missing_core_point_ids, evidence_snippets, explanation."
                ),
            },
        ],
        response_format=DiagnosisResponse,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid diagnosis.")
    return parsed


def run_mock_diagnosis(
    *,
    student_answer: str,
    core_points: list[BetaCorePoint],
) -> DiagnosisResponse:
    """
    Return a deterministic placeholder diagnosis without calling an LLM.

    This is intentionally simple. It exists only to test the UI and data flow before
    connecting the real structured LLM diagnosis in the next checkpoint.
    """
    stripped_answer = student_answer.strip()
    core_point_ids = [core_point.id for core_point in core_points if core_point.id]

    if not stripped_answer:
        return DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            evidence_origin="student_generated",
            is_student_owned_evidence=True,
            task_relevance=0.0,
            correctness=0.0,
            completeness=0.0,
            diagnosis_pattern="off_task",
            missing_core_point_ids=core_point_ids,
            explanation="Mock diagnosis: empty answer treated as off task.",
        )

    return DiagnosisResponse(
        student_intent="answer_attempt",
        is_answer_attempt=True,
        evidence_origin="student_generated",
        is_student_owned_evidence=True,
        task_relevance=0.5,
        correctness=0.0,
        completeness=0.0,
        diagnosis_pattern="unclear",
        missing_core_point_ids=core_point_ids,
        evidence_snippets=[stripped_answer[:120]],
        explanation=(
            "Mock diagnosis: no AI has evaluated the answer yet. All core points are "
            "marked missing so the output panel and ID flow can be tested."
        ),
    )
