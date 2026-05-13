"""LLM-generated tutor feedback and next-question helpers for Beta AI.

The application decides the didactic frame; the LLM only realizes that frame as
natural, student-facing feedback and exactly one next question.
"""

from typing import Literal, cast

import decouple
from openai import AsyncOpenAI
from pydantic import BaseModel

from aitutor.beta_ai.diagnosis import DiagnosisResponse
from aitutor.beta_ai.policy import PolicyPreview
from aitutor.config import get_config
from aitutor.models import BetaCorePoint, BetaMisconception

QuestionLevel = Literal["basic_understanding", "explain_reasoning", "apply_or_compare"]


class TutorTurnResponse(BaseModel):
    """Student-facing tutor turn generated under didactic app constraints."""

    feedback_brief: str = ""
    next_question: str = ""
    question_level: QuestionLevel = "basic_understanding"
    focus_core_point_id: int | None = None
    reveals_answer: bool = False


def choose_question_level(
    diagnosis: DiagnosisResponse, level_status: dict[str, str] | None = None
) -> QuestionLevel:
    """Choose the next reduced Bloom-style level from deterministic app state."""
    if diagnosis.diagnosis_pattern in {"off_task", "unclear", "misconception_present"}:
        return "basic_understanding"
    status = level_status or {}
    if status.get("basic_understanding") != "passed":
        return "basic_understanding"
    if status.get("explain_reasoning") != "passed":
        return "explain_reasoning"
    return "apply_or_compare"


def safe_fallback_tutor_turn(
    *,
    diagnosis: DiagnosisResponse,
    policy_preview: PolicyPreview,
    question_level: QuestionLevel,
) -> TutorTurnResponse:
    """Return a non-leaking fallback if LLM tutor generation fails or leaks."""
    if diagnosis.diagnosis_pattern == "help_seeking":
        feedback = (
            "I can give a small hint, but I cannot count that as your answer yet."
        )
        question = (
            "Think about the role or purpose involved here. What can you "
            "explain in your own words?"
        )
    elif diagnosis.diagnosis_pattern == "misconception_present":
        feedback = (
            "There may be a misunderstanding here, so let's test the idea carefully."
        )
        question = (
            "Can you explain the role or relationship in your own words, "
            "using a small example?"
        )
    elif diagnosis.diagnosis_pattern in {"off_task", "unclear"}:
        feedback = "I cannot yet tell what you understand from that answer."
        question = (
            "Can you explain the main idea in your own words, with one concrete detail?"
        )
    elif diagnosis.diagnosis_pattern == "sufficient_for_completion":
        feedback = "Good, you have covered the main ideas at this level."
        question = (
            "Can you now explain why this idea matters or apply it to a small example?"
        )
    else:
        feedback = (
            policy_preview.feedback_brief
            or "You are on the right track, but one part is still missing."
        )
        question = (
            "Can you expand your answer by explaining the missing role, "
            "relation, or condition in your own words?"
        )

    return TutorTurnResponse(
        feedback_brief=feedback,
        next_question=question,
        question_level=question_level,
        focus_core_point_id=policy_preview.focus_core_point_id,
        reveals_answer=False,
    )


def tutor_turn_reveals_answer(
    tutor_turn: TutorTurnResponse, *, core_points: list[BetaCorePoint]
) -> bool:
    """Heuristically detect direct core-point text leakage in generated questions."""
    combined_text = f"{tutor_turn.feedback_brief} {tutor_turn.next_question}".lower()
    for core_point in core_points:
        core_text = " ".join(core_point.text.lower().split())
        if len(core_text) >= 24 and core_text in combined_text:
            return True
        core_without_punctuation = core_text.rstrip(".?!")
        if (
            len(core_without_punctuation) >= 24
            and core_without_punctuation in combined_text
        ):
            return True
    return tutor_turn.reveals_answer


def _format_core_points(core_points: list[BetaCorePoint]) -> str:
    return (
        "\n".join(
            f"- {core_point.id}: {core_point.text}"
            for core_point in core_points
            if core_point.id
        )
        or "No core points provided."
    )


def _format_misconceptions(misconceptions: list[BetaMisconception]) -> str:
    return (
        "\n".join(
            f"- {misconception.label}"
            for misconception in misconceptions
            if misconception.label
        )
        or "No known misconceptions provided."
    )


async def run_tutor_turn_generation(
    *,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    misconceptions: list[BetaMisconception],
    diagnosis: DiagnosisResponse,
    policy_preview: PolicyPreview,
    question_level: QuestionLevel,
    cumulative_evidence_summary: str,
    current_question: str,
    student_answer: str,
) -> TutorTurnResponse:
    """Generate natural formative feedback and one next question."""
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the student-facing tutor voice in a university AI tutor. "
                    "Use the diagnosis and policy as truth; do not re-grade. "
                    "Give concise, formative feedback and ask exactly one "
                    "next question. Do not reveal the expected core-point "
                    "answer verbatim. Do not show JSON, scores, core point "
                    "IDs, hidden rubrics, or rule IDs to the student. The "
                    "next question should probe understanding at the "
                    "requested question_level. If a student only named a "
                    "keyword, ask for role, relation, function, condition, "
                    "or a small example. If the student asked for a hint, "
                    "example, or the answer, do not provide the full "
                    "solution; give only a small scaffold "
                    "and ask them to try in their own words. If diagnosis_pattern is "
                    "tutor_derived_answer, explain that copied tutor wording "
                    "cannot count yet "
                    "and ask for the student's own wording or a different example."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Concept: {concept_label}\n"
                    f"Concept description: {concept_description}\n\n"
                    "Internal core points, for your guidance only. Do NOT "
                    "copy them verbatim into the student question:\n"
                    f"{_format_core_points(core_points)}\n\n"
                    "Known misconception hints:\n"
                    f"{_format_misconceptions(misconceptions)}\n\n"
                    "Current tutor question: "
                    f"{current_question or 'No previous tutor question yet.'}\n"
                    f"Student answer: {student_answer}\n\n"
                    f"Cumulative evidence summary:\n{cumulative_evidence_summary}\n\n"
                    f"Diagnosis JSON: {diagnosis.model_dump()}\n\n"
                    f"Policy action: {policy_preview.action}\n"
                    f"Policy rationale: {policy_preview.rationale}\n"
                    f"Focus core point id: {policy_preview.focus_core_point_id}\n"
                    f"Requested next question level: {question_level}\n\n"
                    "Return fields: feedback_brief, next_question, question_level, "
                    "focus_core_point_id, reveals_answer. Set "
                    "reveals_answer=true if your "
                    "feedback or question copies an expected core point too directly."
                ),
            },
        ],
        response_format=TutorTurnResponse,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid tutor turn.")
    return parsed
