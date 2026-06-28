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
    diagnosis: DiagnosisResponse,
    level_status: dict[str, str] | None = None,
    current_question_level: QuestionLevel | None = None,
) -> QuestionLevel:
    """Choose the next reduced Bloom-style level from deterministic app state."""
    if (
        diagnosis.diagnosis_pattern == "misconception_present"
        and current_question_level
    ):
        return current_question_level
    if diagnosis.diagnosis_pattern == "off_task":
        return "basic_understanding"
    status = level_status or {}
    if status.get("basic_understanding") != "passed":
        return "basic_understanding"
    if status.get("explain_reasoning") != "passed":
        return "explain_reasoning"
    if status.get("apply_or_compare") != "passed":
        return "apply_or_compare"
    if diagnosis.diagnosis_pattern == "unclear" and current_question_level in {
        "explain_reasoning",
        "apply_or_compare",
    }:
        return current_question_level
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
        if question_level == "apply_or_compare":
            question = (
                "Can you make your application more explicit with one concrete "
                "example, and explain how it connects to the concept?"
            )
        elif question_level == "explain_reasoning":
            question = (
                "Can you make your reasoning more explicit and explain why this "
                "idea matters for the concept?"
            )
        else:
            question = (
                "Can you explain the main idea in your own words, "
                "with one concrete detail?"
            )
    elif diagnosis.diagnosis_pattern == "sufficient_for_completion":
        feedback = "Good, you have covered the main ideas at this level."
        if question_level == "explain_reasoning":
            question = (
                "Can you now explain why this idea matters for the concept, "
                "using your own reasoning?"
            )
        elif question_level == "apply_or_compare":
            question = (
                "Can you apply this idea to a small example or compare it with "
                "a related case?"
            )
        else:
            question = (
                "Can you explain the main idea in your own words, "
                "with one concrete detail?"
            )
    else:
        feedback = (
            policy_preview.feedback_brief
            or "You are on the right track, but one part is still missing."
        )
        if question_level == "apply_or_compare":
            question = (
                "Can you apply the idea to one concrete case or compare it with "
                "a related case, and explain what changes?"
            )
        elif question_level == "explain_reasoning":
            question = (
                "Can you explain why the idea matters or how the parts relate, "
                "using your own reasoning?"
            )
        else:
            question = (
                "Can you expand your answer by explaining the missing role, "
                "relation, or condition in your own words?"
            )

    focus_core_point_id = (
        None
        if question_level in {"explain_reasoning", "apply_or_compare"}
        else policy_preview.focus_core_point_id
    )

    return TutorTurnResponse(
        feedback_brief=feedback,
        next_question=question,
        question_level=question_level,
        focus_core_point_id=focus_core_point_id,
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


async def run_concept_intro_turn_generation(
    *,
    exercise_title: str,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    misconceptions: list[BetaMisconception],
    previous_concept_label: str = "",
    transition_kind: Literal["initial", "automatic", "manual"] = "initial",
) -> TutorTurnResponse:
    """Generate the first tutor turn for a concept without revealing answers."""
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    if transition_kind == "initial":
        transition_instruction = (
            "This is the first tutor message in the chat. Briefly welcome the "
            "student into the exercise and ask exactly one first question."
        )
    elif transition_kind == "automatic":
        transition_instruction = (
            "The student has just completed the previous concept. Briefly acknowledge "
            "that progress, transition naturally to the new concept, and ask exactly "
            "one first question for the new concept."
        )
    else:
        transition_instruction = (
            "The student or tutor switched concepts manually. Briefly orient the "
            "student to the selected concept and ask exactly one first question."
        )

    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate a natural first turn for a university AI tutor. "
                    "The app provides the concept scope, but you must not reveal the "
                    "expected answer. Write concise formative tutor text plus exactly "
                    "one question. The question must be at basic understanding level: "
                    "it should ask the student to explain the concept in their own "
                    "words, describe its role, or give one concrete detail. Do not "
                    "copy core point wording verbatim or near-verbatim. Do not list "
                    "core points as hints. Do not mention hidden rubrics, core point "
                    "IDs, scores, policies, JSON, diagnosis, or Beta internals. Do not "
                    "provide definitions or completed solutions. Set question_level to "
                    "basic_understanding."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Exercise title: {exercise_title}\n"
                    f"Transition kind: {transition_kind}\n"
                    f"Previous concept: {previous_concept_label or 'None'}\n\n"
                    f"Concept: {concept_label}\n"
                    f"Concept description: {concept_description}\n\n"
                    "Internal core points that define the concept scope but must NOT "
                    "be copied into the student-facing turn:\n"
                    f"{_format_core_points(core_points)}\n\n"
                    "Known misconceptions to avoid reinforcing:\n"
                    f"{_format_misconceptions(misconceptions)}\n\n"
                    f"Task: {transition_instruction}\n"
                    "Return fields: feedback_brief, next_question, question_level, "
                    "focus_core_point_id, reveals_answer. Use focus_core_point_id=null "
                    "unless a single broad first core point is clearly the intended "
                    "starting focus. Set reveals_answer=true if your text gives away "
                    "the expected answer too directly."
                ),
            },
        ],
        response_format=TutorTurnResponse,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid concept intro turn.")
    parsed.question_level = "basic_understanding"
    parsed.reveals_answer = tutor_turn_reveals_answer(parsed, core_points=core_points)
    return parsed


async def run_level_transition_question_generation(
    *,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    policy_preview: PolicyPreview,
    next_question_level: QuestionLevel,
) -> TutorTurnResponse:
    """Generate a concept-level question for Basic->Explain or Explain->Apply.

    Unlike ``run_tutor_turn_generation``, this function intentionally does not
    receive the previous tutor question or latest student answer. A level
    transition should be guided by the concept as a whole, not by the final core
    point that happened to complete the previous level.
    """
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    if next_question_level == "explain_reasoning":
        level_task = (
            "Generate an Explain/Reasoning question. Ask the student to explain "
            "why the concept matters, how its main ideas relate, what problem it "
            "solves, what function it has in the theory, or why a simple alternative "
            "would be insufficient. Do not make transfer to a new case or comparison "
            "the main task."
        )
    else:
        level_task = (
            "Generate an Apply/Compare question. Ask the student to use the concept "
            "in a new concrete case, analyze a scenario, decide whether an example "
            "shows the concept, or compare it with a related concept/problem. Do not "
            "ask only for a general explanation of why the concept matters."
        )

    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate the next question for a university AI tutor after "
                    "the student has completed the previous level. Use the provided "
                    "concept label, concept description, and core points only as the "
                    "scope of the concept. Do not ask about one individual core point. "
                    "Do not ask the student to repeat a checklist. Do not mention core "
                    "point IDs, hidden rubrics, scores, policies, or JSON. Ask exactly "
                    "one concise question. The question should be natural and specific "
                    "to the concept as a whole. Do not include the answer structure in "
                    "the question. Do not list several already-covered core ideas as "
                    "hints. Do not name multiple mechanisms the student "
                    "should explain. "
                    "Respect the requested level: Explain/Reasoning should elicit "
                    "causal, functional, or relational understanding; Apply/Compare "
                    "should elicit transfer to a new case or comparison with a related "
                    "case. Do not blur these levels. Set focus_core_point_id=null."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Concept: {concept_label}\n"
                    f"Concept description: {concept_description}\n\n"
                    "Basic core points already covered / concept scope:\n"
                    f"{_format_core_points(core_points)}\n\n"
                    f"Next question level: {next_question_level}\n"
                    f"Level task: {level_task}\n"
                    f"Preferred didactic frame: {policy_preview.suggested_prompt}\n\n"
                    "Return fields: feedback_brief, next_question, question_level, "
                    "focus_core_point_id, reveals_answer. The feedback should briefly "
                    "signal the level transition. The next_question must not focus on "
                    "the last covered basic core point. Keep the question open: do not "
                    "turn the covered core-point list into a set of hints inside the "
                    "question."
                ),
            },
        ],
        response_format=TutorTurnResponse,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid level-transition turn.")
    parsed.question_level = next_question_level
    parsed.focus_core_point_id = None
    parsed.reveals_answer = tutor_turn_reveals_answer(parsed, core_points=core_points)
    return parsed


async def repair_leaky_tutor_turn(
    *,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    policy_preview: PolicyPreview,
    leaky_tutor_turn: TutorTurnResponse,
    question_level: QuestionLevel,
) -> TutorTurnResponse:
    """Rewrite a generated tutor turn once if it reveals expected answer wording."""
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    if question_level == "explain_reasoning":
        level_constraint = (
            "The next question must ask for reasoning: why the concept matters, "
            "how its parts relate, or what function it has. Do not ask for a new "
            "application or comparison as the main task."
        )
    elif question_level == "apply_or_compare":
        level_constraint = (
            "The next question must require application to a concrete case or a "
            "comparison with a related case. Do not ask only for a general explanation."
        )
    else:
        level_constraint = (
            "The next question should elicit a basic explanation in the student's "
            "own words without copying any expected core point wording."
        )

    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You repair a university AI tutor turn that revealed expected "
                    "answer wording too directly. Rewrite it as concise formative "
                    "feedback plus exactly one guiding question. Do not copy any core "
                    "point wording verbatim or near-verbatim. Do not reveal hidden "
                    "rubrics, IDs, policies, scores, JSON, or the expected "
                    "answer. Keep "
                    "the same didactic action and requested question level. Use open "
                    "scaffolding rather than definitions or completed solutions. Do "
                    "not turn a core point into a fill-in-the-blank question. The "
                    "repaired question should ask what makes the idea special, what "
                    "role it plays, what condition should hold, or what the student "
                    "would check, without stating the decisive expected phrase."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Concept: {concept_label}\n"
                    f"Concept description: {concept_description}\n\n"
                    "Internal core points that must NOT be copied into the "
                    "repaired turn:\n"
                    f"{_format_core_points(core_points)}\n\n"
                    f"Policy action: {policy_preview.action}\n"
                    f"Policy rationale: {policy_preview.rationale}\n"
                    f"Requested question level: {question_level}\n"
                    f"Level constraint: {level_constraint}\n\n"
                    "Leaky tutor turn to repair:\n"
                    f"Feedback: {leaky_tutor_turn.feedback_brief}\n"
                    f"Question: {leaky_tutor_turn.next_question}\n\n"
                    "Return fields: feedback_brief, next_question, question_level, "
                    "focus_core_point_id, reveals_answer. Set reveals_answer=true if "
                    "the repaired turn still copies expected answer wording "
                    "too directly."
                ),
            },
        ],
        response_format=TutorTurnResponse,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid repaired tutor turn.")
    parsed.question_level = question_level
    if question_level in {"explain_reasoning", "apply_or_compare"}:
        parsed.focus_core_point_id = None
    parsed.reveals_answer = tutor_turn_reveals_answer(parsed, core_points=core_points)
    return parsed


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
    higher_level_instruction = ""
    if question_level == "explain_reasoning":
        higher_level_instruction = (
            "For this turn, ask a concept-level reasoning question. Do not ask the "
            "student to add one missing core point. The goal is to check why the "
            "concept matters or how its ideas fit together. Set "
            "focus_core_point_id=null."
        )
    elif question_level == "apply_or_compare":
        higher_level_instruction = (
            "For this turn, ask a concept-level transfer question. Ask the student "
            "to apply the concept to a small case or compare it with a related case. "
            "Do not ask for one missing rubric item. Set focus_core_point_id=null."
        )

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
                    "or a small example. If the student asks for help, a hint, "
                    "clarification, an example, or the answer, provide only a "
                    "minimal scaffold that supports the next student-owned attempt. "
                    "Use guiding questions, analogies, or a partial frame rather "
                    "than declarative definitions. Avoid sentences that directly "
                    "state the concept definition, such as 'A directed graph has...' "
                    "or 'The answer is...'. "
                    "Do not answer the current tutor question for the student. "
                    "Do not provide a complete solution, full definition, full "
                    "worked example, or the missing core point verbatim. End by "
                    "asking the student to answer in their own words. If "
                    "a hidden core point says what the expected answer is, do not "
                    "convert that core point into a fill-in-the-blank question. Do "
                    "not include the key predicate, exact condition, or decisive "
                    "phrase from the core point in the question. Ask one level more "
                    "open-ended instead, e.g. about what makes the object special, "
                    "what role it plays, what condition should hold, or what the "
                    "student would check. "
                    "diagnosis_pattern is "
                    "tutor_derived_answer, explain that copied tutor wording "
                    "cannot count yet "
                    "and ask for the student's own wording or a different example. "
                    "For higher-level questions, keep the question focused on the "
                    "whole concept rather than a single hidden core point."
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
                    f"Policy suggested prompt: {policy_preview.suggested_prompt}\n"
                    f"Focus core point id: {policy_preview.focus_core_point_id}\n"
                    "Focus core point text is hidden expected-answer material. Use it "
                    "only to choose the broad direction of the question; do NOT copy, "
                    "paraphrase closely, or turn it into the wording the student "
                    "should produce.\n"
                    f"Requested next question level: {question_level}\n"
                    "Higher-level instruction: "
                    f"{higher_level_instruction or 'None'}\n\n"
                    "Return fields: feedback_brief, next_question, question_level, "
                    "focus_core_point_id, reveals_answer. Set "
                    "reveals_answer=true if your "
                    "feedback or question copies or closely paraphrases an expected "
                    "core point, or if the question already contains the essential "
                    "answer the student should supply."
                ),
            },
        ],
        response_format=TutorTurnResponse,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return a valid tutor turn.")
    if question_level in {"explain_reasoning", "apply_or_compare"}:
        parsed.focus_core_point_id = None
    return parsed
