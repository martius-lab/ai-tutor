"""Deterministic tests for the Beta AI diagnosis control layer."""

from datetime import datetime, timezone

from aitutor.beta_ai.diagnosis import (
    DiagnosisResponse,
    detect_copied_from_tutor,
    validate_and_normalize_diagnosis,
)
from aitutor.beta_ai.policy import preview_policy_action
from aitutor.beta_ai.student_state import (
    build_cumulative_evidence_summary,
    normalized_level_status,
    update_student_concept_state_from_diagnosis,
)
from aitutor.beta_ai.tutor_turn import (
    TutorTurnResponse,
    choose_question_level,
    tutor_turn_reveals_answer,
)
from aitutor.models import BetaCorePoint, BetaMisconception, BetaStudentConceptState


def core_points() -> list[BetaCorePoint]:
    """Return a small binary-search core-point registry for deterministic tests."""
    return [
        BetaCorePoint(
            id=14, beta_concept_id=1, text="Binary search assumes sorted input."
        ),
        BetaCorePoint(
            id=15,
            beta_concept_id=1,
            text="Sorted order allows discarding half the interval.",
        ),
        BetaCorePoint(
            id=16,
            beta_concept_id=1,
            text="Without sorted input, middle comparison is unreliable.",
        ),
    ]


def misconceptions() -> list[BetaMisconception]:
    """Return known misconception hints for deterministic tests."""
    return [
        BetaMisconception(
            id=7,
            beta_concept_id=1,
            label="Binary search works on unsorted arrays.",
        )
    ]


def policy_for(diagnosis: DiagnosisResponse):
    """Validate a raw diagnosis and compute the policy preview."""
    validation_result = validate_and_normalize_diagnosis(
        diagnosis,
        core_points=core_points(),
        student_answer=(
            diagnosis.evidence_snippets[0] if diagnosis.evidence_snippets else ""
        ),
    )
    policy_preview = preview_policy_action(
        validation_result.diagnosis,
        concept_label="Sorted Input Requirement",
        concept_description=(
            "Student understands that binary search relies on sorted input."
        ),
        core_points=core_points(),
        misconceptions=misconceptions(),
    )
    return validation_result, policy_preview


def test_off_task_normalizes_to_refocus_question():
    """Off-task answers should trigger a concept-specific refocus question."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.0,
            correctness=0.0,
            completeness=0.0,
            diagnosis_pattern="sufficient_for_completion",
            evidence_snippets=["I like pizza."],
        )
    )

    assert validation_result.diagnosis.diagnosis_pattern == "off_task"
    assert policy_preview.rule_id == "R-OFFTASK-01"
    assert policy_preview.action == "refocus_question"
    assert "Sorted Input Requirement" in policy_preview.suggested_prompt
    assert "sufficient_for_completion" in validation_result.warnings[-1]


def test_correct_but_incomplete_targets_missing_core_point():
    """Incomplete answers should focus the next question on a missing core point."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.8,
            completeness=0.33,
            diagnosis_pattern="unclear",
            covered_core_point_ids=[14],
            missing_core_point_ids=[15, 16],
            evidence_snippets=["It checks the middle and goes left or right."],
        )
    )

    assert validation_result.diagnosis.diagnosis_pattern == "correct_but_incomplete"
    assert policy_preview.rule_id == "R-INCOMPLETE-01"
    assert policy_preview.action == "ask_targeted_followup"
    assert policy_preview.focus_core_point_id == 15
    assert "Sorted order allows discarding half" in policy_preview.suggested_prompt


def test_misconception_takes_priority_over_incomplete_coverage():
    """Misconceptions should be handled differently from mere omissions."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.3,
            completeness=0.33,
            misconception_flag=True,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[14],
            missing_core_point_ids=[15, 16],
            evidence_snippets=["Binary search works even if the list is unsorted."],
        )
    )

    assert validation_result.diagnosis.diagnosis_pattern == "misconception_present"
    assert policy_preview.rule_id == "R-MISCON-01"
    assert policy_preview.action == "ask_contrast_question"
    assert "misconception" in policy_preview.feedback_brief.lower()


def test_sufficient_for_completion_is_only_potential_completion():
    """High core-point coverage should only preview potential completion."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.95,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[14, 15, 16],
            evidence_snippets=[
                "Binary search assumes sorted input, uses sorted order to "
                "discard half, "
                "and would be unreliable without sorted input."
            ],
        )
    )

    assert validation_result.diagnosis.diagnosis_pattern == "sufficient_for_completion"
    assert policy_preview.rule_id == "R-COMPLETE-PREVIEW-01"
    assert policy_preview.action == "mark_as_potentially_complete"
    assert "preview" in policy_preview.suggested_prompt.lower()


def test_invalid_ids_are_removed_before_policy():
    """Unknown core-point IDs should not leak into downstream policy decisions."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.9,
            correctness=0.8,
            completeness=0.5,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[999],
            missing_core_point_ids=[14],
            evidence_snippets=["Binary search needs sorted input."],
        )
    )

    assert validation_result.diagnosis.covered_core_point_ids == []
    assert 999 not in validation_result.diagnosis.missing_core_point_ids
    assert validation_result.errors
    assert policy_preview.focus_core_point_id == 14


def test_cumulative_evidence_accumulates_core_points_across_turns():
    """Later turns should not erase core points covered in earlier turns."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="unseen",
    )

    first_turn = DiagnosisResponse(
        task_relevance=0.95,
        correctness=0.8,
        completeness=0.33,
        diagnosis_pattern="correct_but_incomplete",
        covered_core_point_ids=[14],
        missing_core_point_ids=[15, 16],
        evidence_snippets=["Binary search assumes sorted input."],
    )
    first_cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=first_turn,
        core_points=core_points(),
        student_answer="Binary search assumes sorted input.",
        trace_reference=1,
        now=datetime.now(timezone.utc),
    )

    assert first_cumulative.covered_core_point_ids == [14]
    assert first_cumulative.missing_core_point_ids == [15, 16]
    assert first_cumulative.diagnosis_pattern == "correct_but_incomplete"

    second_turn = DiagnosisResponse(
        task_relevance=0.95,
        correctness=0.8,
        completeness=0.33,
        diagnosis_pattern="correct_but_incomplete",
        covered_core_point_ids=[15],
        missing_core_point_ids=[14, 16],
        evidence_snippets=["Sorted order allows discarding half the interval."],
    )
    second_cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=second_turn,
        core_points=core_points(),
        student_answer="Sorted order allows discarding half the interval.",
        trace_reference=2,
        now=datetime.now(timezone.utc),
    )
    policy_preview = preview_policy_action(
        second_cumulative,
        concept_label="Sorted Input Requirement",
        concept_description=(
            "Student understands that binary search relies on sorted input."
        ),
        core_points=core_points(),
        misconceptions=misconceptions(),
    )

    assert second_cumulative.covered_core_point_ids == [14, 15]
    assert second_cumulative.missing_core_point_ids == [16]
    assert policy_preview.focus_core_point_id == 16
    assert "14" in student_state.evidence_by_core_point
    assert "15" in student_state.evidence_by_core_point


def test_cumulative_summary_lists_covered_and_missing_core_points():
    """Prompt summary should tell the LLM what is already known and still missing."""
    summary = build_cumulative_evidence_summary(
        core_points=core_points(),
        covered_core_point_ids=[14],
        missing_core_point_ids=[15, 16],
    )

    assert "Covered core points so far" in summary
    assert "14: Binary search assumes sorted input" in summary
    assert "Still missing core points" in summary
    assert "15: Sorted order allows discarding half" in summary


def test_keyword_only_answer_rejected_as_insufficient_evidence():
    """A single keyword should not count as conceptual core-point evidence."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            task_relevance=0.9,
            correctness=0.8,
            completeness=0.33,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[14],
            evidence_snippets=["Binary"],
        )
    )

    assert validation_result.diagnosis.diagnosis_pattern == "shallow_keyword_only"
    assert validation_result.diagnosis.covered_core_point_ids == []
    assert policy_preview.rule_id == "R-SHALLOW-KEYWORD-01"
    assert policy_preview.action == "ask_for_explanation"


def test_tutor_turn_detects_verbatim_core_point_leak():
    """Generated tutor questions should not copy expected core points verbatim."""
    tutor_turn = TutorTurnResponse(
        feedback_brief="Good start.",
        next_question="Can you explain why Binary search assumes sorted input?",
        question_level="basic_understanding",
        focus_core_point_id=14,
    )

    assert tutor_turn_reveals_answer(tutor_turn, core_points=core_points()) is True


def test_basic_level_passes_only_after_all_required_core_points_are_covered():
    """Basic level should require all required core points, not an 80% threshold."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="unseen",
    )

    partial = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.8,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[14, 15],
            evidence_snippets=["sorted input and discarding half"],
        ),
        core_points=core_points(),
        student_answer="Binary search needs sorted input and can discard half.",
        trace_reference=1,
        now=datetime.now(timezone.utc),
        question_level="basic_understanding",
    )

    assert partial.covered_core_point_ids == [14, 15]
    assert (
        normalized_level_status(student_state.level_status)["basic_understanding"]
        == "in_progress"
    )

    complete = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.95,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[16],
            evidence_snippets=["middle comparison is unreliable"],
        ),
        core_points=core_points(),
        student_answer="Without sorted input, middle comparison is unreliable.",
        trace_reference=2,
        now=datetime.now(timezone.utc),
        question_level="basic_understanding",
    )

    assert complete.covered_core_point_ids == [14, 15, 16]
    assert (
        normalized_level_status(student_state.level_status)["basic_understanding"]
        == "passed"
    )
    assert (
        choose_question_level(complete, student_state.level_status)
        == "explain_reasoning"
    )


def test_explain_and_apply_levels_drive_satisfactory_and_secure_state():
    """Concept state should advance via holistic explain/apply success."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="emerging",
        covered_core_point_ids=[14, 15, 16],
        level_status={
            "basic_understanding": "passed",
            "explain_reasoning": "not_started",
            "apply_or_compare": "not_started",
        },
    )

    explain = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.95,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[15],
            missing_core_point_ids=[] ,
            evidence_snippets=["it matters because sorted order makes halving safe"],
        ),
        core_points=core_points(),
        student_answer="It matters because sorted order makes halving safe.",
        trace_reference=3,
        now=datetime.now(timezone.utc),
        question_level="explain_reasoning",
    )

    assert explain.diagnosis_pattern == "correct_but_incomplete"
    assert (
        normalized_level_status(student_state.level_status)["explain_reasoning"]
        == "passed"
    )
    assert student_state.state == "satisfactory"
    assert (
        choose_question_level(explain, student_state.level_status) == "apply_or_compare"
    )

    apply = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.95,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[16],
            missing_core_point_ids=[],
            evidence_snippets=["on an unsorted list this would fail"],
        ),
        core_points=core_points(),
        student_answer=(
            "On an unsorted list this would fail because the discarded half "
            "may contain the target."
        ),
        trace_reference=4,
        now=datetime.now(timezone.utc),
        question_level="apply_or_compare",
    )

    assert apply.diagnosis_pattern == "correct_but_incomplete"
    assert (
        normalized_level_status(student_state.level_status)["apply_or_compare"]
        == "passed"
    )
    assert student_state.state == "secure"


def test_hint_request_is_help_seeking_and_cannot_add_coverage():
    """Hint requests should receive scaffolding but never count as evidence."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            task_relevance=0.9,
            correctness=0.9,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[14, 15, 16],
            evidence_snippets=["gib mir einen hint"],
        )
    )

    assert validation_result.diagnosis.student_intent == "hint_request"
    assert validation_result.diagnosis.is_answer_attempt is False
    assert validation_result.diagnosis.diagnosis_pattern == "help_seeking"
    assert validation_result.diagnosis.covered_core_point_ids == []
    assert policy_preview.rule_id == "R-HELP-SEEKING-01"
    assert policy_preview.action == "give_scaffold_without_progress"


def test_answer_request_does_not_pass_apply_level_even_if_llm_claims_success():
    """Answer requests must not pass apply/compare even if the LLM over-credits them."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="satisfactory",
        covered_core_point_ids=[14, 15, 16],
        level_status={
            "basic_understanding": "passed",
            "explain_reasoning": "passed",
            "apply_or_compare": "not_started",
        },
    )
    validation_result = validate_and_normalize_diagnosis(
        DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            task_relevance=0.95,
            correctness=0.95,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[14, 15, 16],
            evidence_snippets=["give me the answer"],
        ),
        core_points=core_points(),
        student_answer="give me the answer",
    )

    cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=validation_result.diagnosis,
        core_points=core_points(),
        student_answer="give me the answer",
        trace_reference=5,
        now=datetime.now(timezone.utc),
        question_level="apply_or_compare",
    )

    assert cumulative.diagnosis_pattern == "help_seeking"
    assert (
        normalized_level_status(student_state.level_status)["apply_or_compare"]
        == "in_progress"
    )
    assert student_state.state == "satisfactory"


def test_example_request_keeps_existing_coverage_but_adds_no_new_evidence():
    """Example requests may keep previous evidence but must not add new covered IDs."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="emerging",
        covered_core_point_ids=[14],
    )
    validation_result = validate_and_normalize_diagnosis(
        DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            task_relevance=0.95,
            correctness=0.95,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[15, 16],
            evidence_snippets=["give me an example"],
        ),
        core_points=core_points(),
        student_answer="give me an example",
    )

    cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=validation_result.diagnosis,
        core_points=core_points(),
        student_answer="give me an example",
        trace_reference=6,
        now=datetime.now(timezone.utc),
        question_level="basic_understanding",
    )

    assert validation_result.diagnosis.student_intent == "example_request"
    assert cumulative.covered_core_point_ids == [14]
    assert student_state.covered_core_point_ids == [14]


def test_verbatim_tutor_copy_is_not_student_owned_evidence():
    """Copy-pasted tutor examples must not count as mastery evidence."""
    student_answer = (
        "A social network is a graph: people are vertices and friendships are edges."
    )
    conversation_context = [
        {"role": "student", "content": "Can you give me an example?"},
        {"role": "tutor", "content": student_answer},
    ]

    validation_result = validate_and_normalize_diagnosis(
        DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            evidence_origin="student_generated",
            is_student_owned_evidence=True,
            task_relevance=0.95,
            correctness=0.95,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[14, 15, 16],
            evidence_snippets=[student_answer],
        ),
        core_points=core_points(),
        student_answer=student_answer,
        conversation_context=conversation_context,
    )
    policy_preview = preview_policy_action(
        validation_result.diagnosis,
        concept_label="Graph examples",
        concept_description="Student can apply graph terminology to examples.",
        core_points=core_points(),
        misconceptions=misconceptions(),
    )

    assert detect_copied_from_tutor(
        student_answer=student_answer,
        conversation_context=conversation_context,
    )
    assert validation_result.diagnosis.evidence_origin == "copied_from_tutor"
    assert validation_result.diagnosis.is_student_owned_evidence is False
    assert validation_result.diagnosis.diagnosis_pattern == "tutor_derived_answer"
    assert validation_result.diagnosis.covered_core_point_ids == []
    assert validation_result.diagnosis.missing_core_point_ids == [14, 15, 16]
    assert policy_preview.rule_id == "R-TUTOR-DERIVED-01"
    assert policy_preview.action == "ask_for_own_words"


def test_llm_tutor_derived_origin_forces_coverage_removal():
    """Do not trust covered IDs for tutor-derived evidence."""
    validation_result, policy_preview = policy_for(
        DiagnosisResponse(
            student_intent="answer_attempt",
            is_answer_attempt=True,
            evidence_origin="tutor_derived",
            is_student_owned_evidence=True,
            task_relevance=0.95,
            correctness=0.95,
            completeness=1.0,
            diagnosis_pattern="sufficient_for_completion",
            covered_core_point_ids=[14, 15, 16],
            evidence_snippets=["Binary search assumes sorted input."],
        )
    )

    assert validation_result.diagnosis.is_student_owned_evidence is False
    assert validation_result.diagnosis.diagnosis_pattern == "tutor_derived_answer"
    assert validation_result.diagnosis.covered_core_point_ids == []
    assert policy_preview.rule_id == "R-TUTOR-DERIVED-01"


def test_tutor_derived_answer_does_not_update_student_state_or_pass_level():
    """Copied tutor answers must not add new cumulative evidence or pass levels."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="emerging",
        covered_core_point_ids=[14],
        level_status={
            "basic_understanding": "in_progress",
            "explain_reasoning": "not_started",
            "apply_or_compare": "not_started",
        },
    )

    copied_turn = DiagnosisResponse(
        student_intent="answer_attempt",
        is_answer_attempt=True,
        evidence_origin="copied_from_tutor",
        is_student_owned_evidence=False,
        task_relevance=0.95,
        correctness=0.95,
        completeness=0.0,
        diagnosis_pattern="tutor_derived_answer",
        covered_core_point_ids=[],
        missing_core_point_ids=[14, 15, 16],
        evidence_snippets=["Sorted order allows discarding half the interval."],
    )

    cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=copied_turn,
        core_points=core_points(),
        student_answer="Sorted order allows discarding half the interval.",
        trace_reference=7,
        now=datetime.now(timezone.utc),
        question_level="basic_understanding",
    )

    assert cumulative.diagnosis_pattern == "tutor_derived_answer"
    assert cumulative.is_student_owned_evidence is False
    assert cumulative.covered_core_point_ids == [14]
    assert student_state.covered_core_point_ids == [14]
    assert "15" not in student_state.evidence_by_core_point
    assert (
        normalized_level_status(student_state.level_status)["basic_understanding"]
        == "in_progress"
    )


def test_apply_level_does_not_pass_low_correctness_even_with_cumulative_basic_coverage():
    """Apply/compare needs a sufficiently correct current apply answer."""
    student_state = BetaStudentConceptState(
        userinfo_id=1,
        beta_exercise_id=1,
        beta_concept_id=1,
        state="satisfactory",
        covered_core_point_ids=[14, 15, 16],
        level_status={
            "basic_understanding": "passed",
            "explain_reasoning": "passed",
            "apply_or_compare": "in_progress",
        },
    )

    incomplete_apply_turn = DiagnosisResponse(
        student_intent="answer_attempt",
        is_answer_attempt=True,
        evidence_origin="student_generated",
        is_student_owned_evidence=True,
        task_relevance=1.0,
        correctness=0.6,
        completeness=1.0,
        diagnosis_pattern="correct_but_incomplete",
        covered_core_point_ids=[14, 15, 16],
        missing_core_point_ids=[],
        evidence_snippets=[
            "I would represent the cities as vertices and the connection as an edge."
        ],
    )

    cumulative = update_student_concept_state_from_diagnosis(
        student_state=student_state,
        latest_diagnosis=incomplete_apply_turn,
        core_points=core_points(),
        student_answer=(
            "I would represent the cities as vertices and the connection as an edge."
        ),
        trace_reference=8,
        now=datetime.now(timezone.utc),
        question_level="apply_or_compare",
    )
    policy_preview = preview_policy_action(
        cumulative,
        concept_label="Definition of a Graph",
        concept_description="A graph models pairwise relations between objects.",
        core_points=core_points(),
        misconceptions=misconceptions(),
    )

    assert cumulative.diagnosis_pattern == "correct_but_incomplete"
    assert (
        normalized_level_status(student_state.level_status)["apply_or_compare"]
        == "in_progress"
    )
    assert student_state.state == "satisfactory"
    assert policy_preview.action == "ask_holistic_explanation"
    assert policy_preview.focus_core_point_id is None


def test_policy_does_not_fallback_to_first_core_point_when_no_missing_ids():
    """No missing IDs means no targeted follow-up on core point 1/first point."""
    policy_preview = preview_policy_action(
        DiagnosisResponse(
            task_relevance=0.95,
            correctness=0.65,
            completeness=1.0,
            diagnosis_pattern="correct_but_incomplete",
            covered_core_point_ids=[14, 15, 16],
            missing_core_point_ids=[],
            evidence_snippets=["I can explain the overall idea but need to connect it."],
        ),
        concept_label="Sorted Input Requirement",
        concept_description=(
            "Student understands that binary search relies on sorted input."
        ),
        core_points=core_points(),
        misconceptions=misconceptions(),
    )

    assert policy_preview.rule_id == "R-HOLISTIC-EXPLAIN-01"
    assert policy_preview.action == "ask_holistic_explanation"
    assert policy_preview.focus_core_point_id is None
    assert "14" not in policy_preview.suggested_prompt
