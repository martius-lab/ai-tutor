"""Policy preview helpers for the Beta AI Tutor diagnosis lab."""

from typing import Literal

from pydantic import BaseModel

from aitutor.beta_ai.diagnosis import DiagnosisResponse
from aitutor.models import BetaCorePoint, BetaMisconception

DidacticAction = Literal[
    "refocus_question",
    "give_scaffold_without_progress",
    "ask_for_own_words",
    "ask_targeted_followup",
    "ask_holistic_explanation",
    "ask_application_or_comparison",
    "ask_contrast_question",
    "mark_as_potentially_complete",
    "ask_for_explanation",
    "ask_clarification",
]


class PolicyPreview(BaseModel):
    """Preview of the next didactic action implied by a diagnosis pattern."""

    rule_id: str
    action: DidacticAction
    rationale: str
    focus_core_point_id: int | None = None
    focus_core_point_text: str = ""
    feedback_brief: str = ""
    suggested_prompt: str


def _core_point_by_id(core_points: list[BetaCorePoint]) -> dict[int, BetaCorePoint]:
    """Return persisted core points indexed by database ID."""
    return {core_point.id: core_point for core_point in core_points if core_point.id}


def _select_focus_core_point(
    diagnosis: DiagnosisResponse,
    core_points: list[BetaCorePoint],
) -> BetaCorePoint | None:
    """Select the highest-priority missing core point, if one exists."""
    core_points_by_id = _core_point_by_id(core_points)
    for core_point_id in diagnosis.missing_core_point_ids:
        if core_point_id in core_points_by_id:
            return core_points_by_id[core_point_id]
    return None


def _covered_summary(
    diagnosis: DiagnosisResponse, core_points: list[BetaCorePoint]
) -> str:
    """Create a short human-readable summary of covered core points."""
    core_points_by_id = _core_point_by_id(core_points)
    covered_texts = [
        core_points_by_id[core_point_id].text
        for core_point_id in diagnosis.covered_core_point_ids[:2]
        if core_point_id in core_points_by_id
    ]
    if not covered_texts:
        return "I cannot yet identify a clearly covered core point."
    if len(covered_texts) == 1:
        return f"You addressed this core idea: {covered_texts[0]}"
    return "You addressed these core ideas: " + "; ".join(covered_texts)


def preview_policy_action(
    diagnosis: DiagnosisResponse,
    *,
    concept_label: str,
    concept_description: str,
    core_points: list[BetaCorePoint],
    misconceptions: list[BetaMisconception],
) -> PolicyPreview:
    """Map a normalized diagnosis pattern to a context-aware didactic action preview."""
    focus_core_point = _select_focus_core_point(diagnosis, core_points)
    focus_core_point_id = focus_core_point.id if focus_core_point else None
    focus_core_point_text = focus_core_point.text if focus_core_point else ""
    concept_reference = concept_label or concept_description or "the selected concept"

    if diagnosis.diagnosis_pattern == "off_task":
        return PolicyPreview(
            rule_id="R-OFFTASK-01",
            action="refocus_question",
            rationale=(
                "The answer is empty, off-topic, or does not cover any "
                "selected core point. The next step should re-anchor the "
                "student in the current concept before "
                "continuing diagnosis."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=(
                f"Your answer does not yet address '{concept_reference}' directly."
            ),
            suggested_prompt=(
                f"Let's return to '{concept_reference}'. In one sentence, "
                "what is the key idea behind this concept"
                + (
                    f", especially: {focus_core_point_text}?"
                    if focus_core_point_text
                    else "?"
                )
            ),
        )

    if diagnosis.diagnosis_pattern == "help_seeking":
        return PolicyPreview(
            rule_id="R-HELP-SEEKING-01",
            action="give_scaffold_without_progress",
            rationale=(
                "The student is asking for help, a hint, an example, or the "
                "answer rather than attempting the current question. The "
                "tutor may scaffold, but this turn must not "
                "count as performance evidence or level progress."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=(
                "I can help with a small scaffold, but I need your own "
                "attempt for progress."
            ),
            suggested_prompt=(
                "What part can you explain in your own words after this hint?"
            ),
        )

    if diagnosis.diagnosis_pattern == "tutor_derived_answer":
        return PolicyPreview(
            rule_id="R-TUTOR-DERIVED-01",
            action="ask_for_own_words",
            rationale=(
                "The answer appears to repeat tutor-provided wording or an "
                "example. It may be useful practice, but it is not "
                "student-owned evidence and must not advance mastery."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=(
                "That is very close to something I provided, so I need your "
                "own explanation."
            ),
            suggested_prompt=(
                "Can you explain the same idea in your own words or use a "
                "different example?"
            ),
        )

    if diagnosis.diagnosis_pattern == "misconception_present":
        misconception_hint = (
            misconceptions[0].label
            if misconceptions
            else "the assumption in your answer"
        )
        return PolicyPreview(
            rule_id="R-MISCON-01",
            action="ask_contrast_question",
            rationale=(
                "The diagnosis indicates a likely misconception rather than "
                "only missing detail. A contrast question is preferred "
                "because misconceptions require conceptual "
                "restructuring, not just adding omitted information."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=(
                f"There may be a misconception related to '{misconception_hint}'."
            ),
            suggested_prompt=(
                "Let's test that idea with a contrasting case. "
                + (
                    "How would your answer change if we focus on this core "
                    f"point: {focus_core_point_text}?"
                    if focus_core_point_text
                    else "What example would show whether "
                    f"'{misconception_hint}' is actually true?"
                )
            ),
        )

    if diagnosis.diagnosis_pattern == "shallow_keyword_only":
        return PolicyPreview(
            rule_id="R-SHALLOW-KEYWORD-01",
            action="ask_for_explanation",
            rationale=(
                "The answer contains too little conceptual evidence. A "
                "keyword or short phrase is not enough to count as "
                "understanding; the next step should ask for role, "
                "relation, function, condition, or an example."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=(
                "You named something relevant, but I still need to see what "
                "you understand about it."
            ),
            suggested_prompt=(
                "Can you explain the role, relationship, or purpose in your own words?"
            ),
        )

    if diagnosis.diagnosis_pattern == "correct_but_incomplete":
        if not diagnosis.missing_core_point_ids:
            return PolicyPreview(
                rule_id="R-HOLISTIC-EXPLAIN-01",
                action="ask_holistic_explanation",
                rationale=(
                    "The cumulative concept coverage has no missing core "
                    "points, but the current higher-level response still needs "
                    "a concept-level explanation or transfer check. The next "
                    "step should not fall back to the first core point."
                ),
                feedback_brief=_covered_summary(diagnosis, core_points),
                suggested_prompt=(
                    f"Can you explain why '{concept_reference}' matters, "
                    "using the idea in your own words rather than listing details?"
                ),
            )

        return PolicyPreview(
            rule_id="R-INCOMPLETE-01",
            action="ask_targeted_followup",
            rationale=(
                "The answer covers at least one core point, but important "
                "required points are still missing. A targeted follow-up on "
                "the highest-priority missing core point "
                "is the most formative next step."
            ),
            focus_core_point_id=focus_core_point_id,
            focus_core_point_text=focus_core_point_text,
            feedback_brief=_covered_summary(diagnosis, core_points),
            suggested_prompt=(
                f"Can you add the missing part: {focus_core_point_text}?"
                if focus_core_point_text
                else "Can you add the missing core idea that explains why this works?"
            ),
        )

    if diagnosis.diagnosis_pattern == "sufficient_for_completion":
        return PolicyPreview(
            rule_id="R-COMPLETE-PREVIEW-01",
            action="mark_as_potentially_complete",
            rationale=(
                "The answer covers enough core points and no misconception "
                "was detected. This is only a preview because final "
                "completion should later consider student state "
                "and independent evidence across turns."
            ),
            feedback_brief=_covered_summary(diagnosis, core_points),
            suggested_prompt=(
                "This answer could be accepted for this concept in the "
                "Diagnosis Lab preview."
            ),
        )

    return PolicyPreview(
        rule_id="R-UNCLEAR-01",
        action="ask_clarification",
        rationale=(
            "The diagnosis is unclear or has too little reliable evidence "
            "for a stronger action."
        ),
        focus_core_point_id=focus_core_point_id,
        focus_core_point_text=focus_core_point_text,
        feedback_brief=(
            f"Your answer may relate to '{concept_reference}', but the "
            "relevant core point is not clear yet."
        ),
        suggested_prompt=(
            "Can you explain your reasoning more concretely and connect it "
            f"to '{concept_reference}'?"
        ),
    )
