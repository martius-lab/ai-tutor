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
    "advance_to_next_concept",
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
                f"Refocus the student on '{concept_reference}' with one concise, "
                "open question about the concept's key idea. "
                + (
                    "Use focus_core_point_text only as hidden direction; do not "
                    "quote, closely paraphrase, or reveal it directly."
                    if focus_core_point_text
                    else "Do not introduce expected-answer wording as a hint."
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
                "Give one small orienting cue without solving the task, then ask "
                "for one student-owned attempt in the student's own words."
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
                "Ask for the same idea in the student's own words or for a "
                "different self-generated example; do not count copied wording."
            ),
        )

    if diagnosis.diagnosis_pattern == "misconception_present":
        misconception_hint = (
            diagnosis.misconception_label or misconceptions[0].label
            if misconceptions or diagnosis.misconception_label
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
                "Ask a contrastive question that makes the student test their "
                "assumption against a concrete case or consequence. "
                + (
                    "Use focus_core_point_text as the hidden target idea, but do "
                    "not quote, closely paraphrase, or reveal it directly."
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
                "Ask the student to explain the role, relationship, function, "
                "or purpose in their own words, using one concrete detail."
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
                    f"Ask the student to improve the higher-level explanation of "
                    f"'{concept_reference}' by connecting it to a conceptual "
                    "consequence, limitation, model choice, or naive alternative. "
                    "Do not ask for an already covered basic mechanism, condition, "
                    "or effect again."
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
                "Use focus_core_point_text as the hidden target. Ask one open "
                "follow-up that elicits the underlying role, condition, relation, "
                "or example without quoting or closely paraphrasing the target wording."
                if focus_core_point_text
                else "Ask for the missing core idea through an open guiding question."
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


def policy_preview_for_next_level(
    *,
    concept_label: str,
    concept_description: str,
    next_question_level: str,
) -> PolicyPreview | None:
    """Return a level-transition policy preview when state already advanced.

    The normal diagnosis-pattern policy explains how to repair or respond to the
    current diagnosis. After a level passes, however, the next didactic action is
    governed by level state: Basic -> Explain, Explain -> Apply. This helper keeps
    audit traces aligned with the generated next question level.
    """
    concept_reference = concept_label or concept_description or "the selected concept"
    if next_question_level == "explain_reasoning":
        return PolicyPreview(
            rule_id="R-ASK-HOLISTIC-EXPLAIN-01",
            action="ask_holistic_explanation",
            rationale=(
                "Basic core-point coverage is complete. The next didactic step "
                "is a concept-level explanation prompt that asks for reasoning."
            ),
            feedback_brief=(
                "Good, the basic ideas are covered. Now check the student's reasoning "
                "about the concept as a whole."
            ),
            suggested_prompt=(
                f"Ask for a concept-level self-explanation of '{concept_reference}': "
                "the student should explain a conceptual consequence, epistemic "
                "consequence, modeling implication, boundary of interpretation, "
                "evidence need, or how one would distinguish between two possible "
                "explanations. Treat covered "
                "core points as forbidden main-question intents: do not ask why a "
                "covered mechanism matters, do not ask for an already covered "
                "core-point mechanism, how a covered mechanism helps, how a "
                "covered effect is achieved, or why an already-covered solution "
                "avoids an already-covered problem. The main question must require "
                "a new reasoning move, not restate or ask for a why/how "
                "reformulation of Basic evidence."
            ),
        )
    if next_question_level == "apply_or_compare":
        return PolicyPreview(
            rule_id="R-ASK-APPLY-01",
            action="ask_application_or_comparison",
            rationale=(
                "The explanation level is complete. The next didactic step is "
                "an application, comparison, or transfer prompt for the concept."
            ),
            feedback_brief=(
                "Good explanation. Now check whether the student can transfer the "
                "concept to a new situation."
            ),
            suggested_prompt=(
                f"Ask the student to use '{concept_reference}' in one new transfer "
                "or comparison task. The question should require judging what extra "
                "evidence is needed, contrasting two interpretations, predicting an "
                "observable consequence, or deciding between explanations in a new "
                "case. Treat covered core points as forbidden main-question intents: "
                "not repeating covered core-point mechanisms; do not ask the student "
                "to directly apply a covered mechanism, condition, effect, purpose, "
                "or problem-solution relation. The new case should require a judgment "
                "or evidence decision rather than recycling Basic evidence as an "
                "application prompt."
            ),
        )
    return None


def policy_preview_for_level_repair(
    *,
    diagnosis: DiagnosisResponse,
    concept_label: str,
    concept_description: str,
    question_level: str,
) -> PolicyPreview | None:
    """Return a level-specific repair policy for active Explain/Apply questions.

    The normal diagnosis-pattern policy is level-agnostic. Once a student is
    working on Explain or Apply/Compare, however, weak or invalid answers should
    repair that same cognitive operation instead of falling back to Basic.
    """
    concept_reference = concept_label or concept_description or "the selected concept"
    pattern = diagnosis.diagnosis_pattern

    if question_level == "explain_reasoning":
        if pattern == "off_task":
            return PolicyPreview(
                rule_id="R-EXPLAIN-REFOCUS-OFFTASK-01",
                action="ask_holistic_explanation",
                rationale=(
                    "The student did not answer the active Explain question. The "
                    "repair should stay at Explain level and re-anchor the requested "
                    "reasoning task instead of asking for a Basic definition."
                ),
                feedback_brief=(
                    "Your answer does not yet address the explanation question."
                ),
                suggested_prompt=(
                    f"Re-anchor the Explain task for '{concept_reference}'. Ask one "
                    "concise question about a conceptual consequence, relationship, "
                    "modeling implication, or why a naive alternative is incomplete. "
                    "Do not ask for a Basic definition or a covered core point."
                ),
            )
        if pattern == "shallow_keyword_only":
            return PolicyPreview(
                rule_id="R-EXPLAIN-SHALLOW-01",
                action="ask_for_explanation",
                rationale=(
                    "The student gave only a thin keyword-level response to an "
                    "Explain question. The next step should elicit reasoning beyond "
                    "the keyword."
                ),
                feedback_brief=(
                    "You named something relevant, but not the reasoning yet."
                ),
                suggested_prompt=(
                    f"Ask the student to turn the keyword into an Explain-level "
                    f"self-explanation for '{concept_reference}': what consequence, "
                    "relation, or modeling implication follows from it? Do not ask "
                    "for a list or Basic restatement."
                ),
            )
        if pattern == "help_seeking":
            return PolicyPreview(
                rule_id="R-EXPLAIN-HELP-SEEKING-01",
                action="give_scaffold_without_progress",
                rationale=(
                    "The student asks for help during Explain. Provide a small "
                    "reasoning scaffold, but do not count it as progress."
                ),
                feedback_brief=(
                    "I can give a small reasoning scaffold, but I still need your own "
                    "explanation."
                ),
                suggested_prompt=(
                    f"Give one small Explain-level scaffold for '{concept_reference}' "
                    "without solving it, then ask the student to explain one "
                    "consequence, relation, or naive alternative in their own words."
                ),
            )
        if pattern == "misconception_present":
            return PolicyPreview(
                rule_id="R-EXPLAIN-MISCONCEPTION-01",
                action="ask_contrast_question",
                rationale=(
                    "The active Explain answer contains a misconception. A contrast "
                    "or naive-alternative question supports conceptual change."
                ),
                feedback_brief=(
                    "There may be a mistaken assumption in your explanation."
                ),
                suggested_prompt=(
                    f"Ask a contrastive Explain-level question for "
                    f"'{concept_reference}' "
                    "that tests the student's assumption against a consequence or "
                    "naive alternative. Do not state the correct explanation directly."
                ),
            )
        if pattern == "tutor_derived_answer":
            return PolicyPreview(
                rule_id="R-EXPLAIN-TUTOR-DERIVED-01",
                action="ask_for_own_words",
                rationale=(
                    "The Explain answer appears derived from tutor wording. It must "
                    "be reformulated as student-owned reasoning."
                ),
                feedback_brief="That is too close to tutor wording to count yet.",
                suggested_prompt=(
                    f"Ask the student to explain a consequence or relationship of "
                    f"'{concept_reference}' in their own words, without reusing tutor "
                    "phrasing."
                ),
            )
        if pattern == "correct_but_incomplete":
            return PolicyPreview(
                rule_id="R-EXPLAIN-INCOMPLETE-01",
                action="ask_holistic_explanation",
                rationale=(
                    "The Explain answer is partly relevant but not yet strong enough "
                    "for the level. Ask for a stronger concept-level connection."
                ),
                feedback_brief=(
                    "Your explanation is partly on track, but it needs a clearer "
                    "connection."
                ),
                suggested_prompt=(
                    f"Ask the student to strengthen the Explain answer for "
                    f"'{concept_reference}' by connecting it to a consequence, "
                    "limitation, model choice, or naive alternative. Do not ask for "
                    "a Basic core-point mechanism again."
                ),
            )
        if pattern == "unclear":
            return PolicyPreview(
                rule_id="R-EXPLAIN-CLARIFY-01",
                action="ask_clarification",
                rationale=(
                    "The Explain answer may be relevant, but the reasoning is not "
                    "diagnostically clear. Ask for a precise relation or consequence."
                ),
                feedback_brief="I cannot yet see the reasoning clearly enough.",
                suggested_prompt=(
                    f"Ask one clarification question at Explain level for "
                    f"'{concept_reference}': which relation, consequence, or "
                    "modeling implication does the student mean?"
                ),
            )

    if question_level == "apply_or_compare":
        if pattern == "off_task":
            return PolicyPreview(
                rule_id="R-APPLY-REFOCUS-OFFTASK-01",
                action="ask_application_or_comparison",
                rationale=(
                    "The student did not answer the active Apply/Compare scenario. "
                    "The repair should re-anchor the same transfer/comparison task "
                    "instead of asking for Basic knowledge."
                ),
                feedback_brief=(
                    "Your answer does not yet address the application scenario."
                ),
                suggested_prompt=(
                    f"Re-anchor the current Apply/Compare task for "
                    f"'{concept_reference}'. "
                    "Do not ask for a Basic definition. Ask one scenario-based "
                    "question about what changes, what must be judged, what follows, "
                    "or what comparison should be made in the current case."
                ),
            )
        if pattern == "shallow_keyword_only":
            return PolicyPreview(
                rule_id="R-APPLY-SHALLOW-01",
                action="ask_application_or_comparison",
                rationale=(
                    "The student gave a keyword-like response to Apply/Compare. The "
                    "next step should require using that idea in the scenario."
                ),
                feedback_brief=(
                    "You named something relevant, but you have not applied it to "
                    "the case yet."
                ),
                suggested_prompt=(
                    f"Ask the student to use the named idea from '{concept_reference}' "
                    "in the current scenario: what changes, what would they compare, "
                    "or what decision follows? Do not ask for a Basic restatement."
                ),
            )
        if pattern == "help_seeking":
            return PolicyPreview(
                rule_id="R-APPLY-HELP-SEEKING-01",
                action="give_scaffold_without_progress",
                rationale=(
                    "The student asks for help during Apply/Compare. Provide a small "
                    "scenario scaffold, but require a student-owned transfer answer."
                ),
                feedback_brief=(
                    "I can give a small orientation, but the application still needs "
                    "to be your own answer."
                ),
                suggested_prompt=(
                    f"Give one minimal scenario cue for applying '{concept_reference}' "
                    "without solving the case, then ask what changes, what should be "
                    "compared, or what decision follows."
                ),
            )
        if pattern == "misconception_present":
            return PolicyPreview(
                rule_id="R-APPLY-MISCONCEPTION-01",
                action="ask_contrast_question",
                rationale=(
                    "The Apply/Compare answer contains a misconception. A contrast "
                    "inside the scenario is preferred over direct correction."
                ),
                feedback_brief=(
                    "There may be a mistaken assumption in how you applied the concept."
                ),
                suggested_prompt=(
                    f"Ask a scenario-based contrast question for '{concept_reference}' "
                    "that compares the student's assumption with a countercase or "
                    "related case. Do not give the correct application directly."
                ),
            )
        if pattern == "tutor_derived_answer":
            return PolicyPreview(
                rule_id="R-APPLY-TUTOR-DERIVED-01",
                action="ask_for_own_words",
                rationale=(
                    "The Apply/Compare answer appears derived from tutor wording. It "
                    "must be re-applied in the student's own words."
                ),
                feedback_brief="That is too close to tutor wording to count yet.",
                suggested_prompt=(
                    f"Ask the student to apply or compare '{concept_reference}' in "
                    "the current case using their own words, including what changes "
                    "or what decision follows."
                ),
            )
        if pattern == "correct_but_incomplete":
            return PolicyPreview(
                rule_id="R-APPLY-INCOMPLETE-01",
                action="ask_application_or_comparison",
                rationale=(
                    "The Apply/Compare answer is partly relevant but does not yet "
                    "complete the transfer or comparison."
                ),
                feedback_brief=(
                    "Your application is partly on track, but the transfer is not "
                    "complete yet."
                ),
                suggested_prompt=(
                    f"Ask the student to complete the Apply/Compare answer for "
                    f"'{concept_reference}' by naming the concrete change, contrast, "
                    "prediction, or decision in the scenario and briefly why it "
                    "follows."
                ),
            )
        if pattern == "unclear":
            return PolicyPreview(
                rule_id="R-APPLY-CLARIFY-01",
                action="ask_clarification",
                rationale=(
                    "The Apply/Compare answer may relate to the scenario, but the "
                    "transfer or comparison is unclear."
                ),
                feedback_brief=(
                    "I cannot yet see how your answer applies to the scenario."
                ),
                suggested_prompt=(
                    f"Ask one clarification question at Apply/Compare level for "
                    f"'{concept_reference}': what scenario change, comparison, "
                    "prediction, or decision does the student mean?"
                ),
            )

    return None
