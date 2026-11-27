"""Audit trace preview schemas for the Beta AI Tutor diagnosis lab."""

import json

from pydantic import BaseModel, Field

from aitutor.beta_ai.diagnosis import DiagnosisResponse
from aitutor.beta_ai.policy import PolicyPreview


class DiagnosisTrace(BaseModel):
    """Replayable preview of one diagnosis and policy decision."""

    exercise_title: str = ""
    concept_label: str = ""
    concept_description: str = ""
    student_answer: str = ""
    llm_suggested_pattern: str = ""
    final_pattern: str = ""
    task_relevance: float = 0.0
    correctness: float = 0.0
    completeness: float = 0.0
    misconception_flag: bool = False
    covered_core_point_ids: list[int] = Field(default_factory=list)
    missing_core_point_ids: list[int] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    selected_rule_id: str = ""
    selected_action: str = ""
    focus_core_point_id: int | None = None
    focus_core_point_text: str = ""
    feedback_brief: str = ""
    suggested_prompt: str = ""

    def to_pretty_json(self) -> str:
        """Return a deterministic JSON representation for display/replay."""
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False)


def build_diagnosis_trace(
    *,
    exercise_title: str,
    concept_label: str,
    concept_description: str,
    student_answer: str,
    diagnosis: DiagnosisResponse,
    llm_suggested_pattern: str,
    validation_errors: list[str],
    validation_warnings: list[str],
    policy_preview: PolicyPreview,
) -> DiagnosisTrace:
    """Build a replayable trace preview from validated diagnosis and policy output."""
    return DiagnosisTrace(
        exercise_title=exercise_title,
        concept_label=concept_label,
        concept_description=concept_description,
        student_answer=student_answer,
        llm_suggested_pattern=llm_suggested_pattern,
        final_pattern=diagnosis.diagnosis_pattern,
        task_relevance=diagnosis.task_relevance,
        correctness=diagnosis.correctness,
        completeness=diagnosis.completeness,
        misconception_flag=diagnosis.misconception_flag,
        covered_core_point_ids=diagnosis.covered_core_point_ids,
        missing_core_point_ids=diagnosis.missing_core_point_ids,
        evidence_snippets=diagnosis.evidence_snippets,
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        selected_rule_id=policy_preview.rule_id,
        selected_action=policy_preview.action,
        focus_core_point_id=policy_preview.focus_core_point_id,
        focus_core_point_text=policy_preview.focus_core_point_text,
        feedback_brief=policy_preview.feedback_brief,
        suggested_prompt=policy_preview.suggested_prompt,
    )
