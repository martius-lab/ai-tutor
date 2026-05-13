"""State for the Beta AI diagnosis lab skeleton."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.beta_ai.audit import DiagnosisTrace, build_diagnosis_trace
from aitutor.beta_ai.diagnosis import (
    DiagnosisResponse,
    run_llm_diagnosis,
    run_mock_diagnosis,
    validate_and_normalize_diagnosis,
)
from aitutor.beta_ai.policy import PolicyPreview, preview_policy_action
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaMisconception,
    UserRole,
)


class BetaAIDiagnosisLabState(SessionState):
    """State for inspecting Beta AI concept data before diagnosis is implemented."""

    beta_exercises: list[BetaExercise] = []
    concepts: list[BetaConcept] = []
    core_points: list[BetaCorePoint] = []
    misconceptions: list[BetaMisconception] = []
    selected_exercise_id: int | None = None
    selected_exercise_title: str = ""
    selected_concept_id: int | None = None
    selected_concept_label: str = ""
    selected_concept_description: str = ""
    student_answer: str = ""
    diagnosis: DiagnosisResponse | None = None
    llm_suggested_pattern: str = ""
    diagnosis_validation_errors: list[str] = []
    diagnosis_validation_warnings: list[str] = []
    policy_preview: PolicyPreview | None = None
    diagnosis_trace: DiagnosisTrace | None = None
    running_llm_diagnosis: bool = False

    @rx.event
    def set_student_answer(self, value: str):
        """Set the example student answer for the future diagnosis step."""
        self.student_answer = value

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialize the diagnosis lab."""
        self.global_load()
        self.reset_selection()
        self.load_beta_exercises()

    def on_logout(self):
        """Clear page-specific state on logout."""
        self.beta_exercises = []
        self.reset_selection()

    @rx.var
    def has_selected_exercise(self) -> bool:
        """Whether an exercise has been selected."""
        return self.selected_exercise_id is not None

    @rx.var
    def has_selected_concept(self) -> bool:
        """Whether a concept has been selected."""
        return self.selected_concept_id is not None

    @rx.var
    def has_diagnosis(self) -> bool:
        """Whether a mock diagnosis has been created."""
        return self.diagnosis is not None

    @rx.var
    def can_run_diagnosis(self) -> bool:
        """Whether the real LLM diagnosis can be triggered."""
        return bool(
            self.selected_concept_id is not None
            and self.student_answer.strip()
            and not self.running_llm_diagnosis
        )

    @rx.var
    def diagnosis_pattern(self) -> str:
        """Return diagnosis pattern for display."""
        return self.diagnosis.diagnosis_pattern if self.diagnosis else ""

    @rx.var
    def has_validation_messages(self) -> bool:
        """Whether validation produced errors or warnings."""
        return bool(
            self.diagnosis_validation_errors or self.diagnosis_validation_warnings
        )

    @rx.var
    def has_policy_preview(self) -> bool:
        """Whether a policy preview has been computed."""
        return self.policy_preview is not None

    @rx.var
    def has_diagnosis_trace(self) -> bool:
        """Whether an audit trace preview has been built."""
        return self.diagnosis_trace is not None

    @rx.var
    def diagnosis_trace_json(self) -> str:
        """Return the current audit trace preview as pretty JSON."""
        return self.diagnosis_trace.to_pretty_json() if self.diagnosis_trace else ""

    @rx.var
    def policy_preview_action(self) -> str:
        """Return the previewed policy action for display."""
        return self.policy_preview.action if self.policy_preview else ""

    @rx.var
    def policy_preview_rule_id(self) -> str:
        """Return the previewed policy rule id for display."""
        return self.policy_preview.rule_id if self.policy_preview else ""

    @rx.var
    def policy_preview_focus_core_point(self) -> str:
        """Return the previewed focus core point for display."""
        if not self.policy_preview or self.policy_preview.focus_core_point_id is None:
            return ""
        return (
            f"{self.policy_preview.focus_core_point_id}: "
            f"{self.policy_preview.focus_core_point_text}"
        )

    @rx.var
    def policy_preview_feedback_brief(self) -> str:
        """Return the previewed feedback brief for display."""
        return self.policy_preview.feedback_brief if self.policy_preview else ""

    @rx.var
    def policy_preview_rationale(self) -> str:
        """Return the previewed policy rationale for display."""
        return self.policy_preview.rationale if self.policy_preview else ""

    @rx.var
    def policy_preview_suggested_prompt(self) -> str:
        """Return the previewed tutor prompt for display."""
        return self.policy_preview.suggested_prompt if self.policy_preview else ""

    @rx.var
    def diagnosis_validation_errors_text(self) -> str:
        """Return validation errors for display."""
        return "\n".join(self.diagnosis_validation_errors)

    @rx.var
    def diagnosis_validation_warnings_text(self) -> str:
        """Return validation warnings for display."""
        return "\n".join(self.diagnosis_validation_warnings)

    @rx.var
    def diagnosis_task_relevance(self) -> str:
        """Return task relevance score for display."""
        return str(self.diagnosis.task_relevance) if self.diagnosis else ""

    @rx.var
    def diagnosis_correctness(self) -> str:
        """Return correctness score for display."""
        return str(self.diagnosis.correctness) if self.diagnosis else ""

    @rx.var
    def diagnosis_completeness(self) -> str:
        """Return completeness score for display."""
        return str(self.diagnosis.completeness) if self.diagnosis else ""

    @rx.var
    def diagnosis_missing_core_point_ids(self) -> str:
        """Return missing core point ids for display."""
        return str(self.diagnosis.missing_core_point_ids) if self.diagnosis else ""

    @rx.var
    def diagnosis_covered_core_point_ids(self) -> str:
        """Return covered core point ids for display."""
        return str(self.diagnosis.covered_core_point_ids) if self.diagnosis else ""

    @rx.var
    def diagnosis_evidence_snippets(self) -> str:
        """Return evidence snippets for display."""
        return str(self.diagnosis.evidence_snippets) if self.diagnosis else ""

    @rx.var
    def diagnosis_explanation(self) -> str:
        """Return diagnosis explanation for display."""
        return self.diagnosis.explanation if self.diagnosis else ""

    def reset_selection(self):
        """Reset selected exercise, concept and loaded child data."""
        self.concepts = []
        self.core_points = []
        self.misconceptions = []
        self.selected_exercise_id = None
        self.selected_exercise_title = ""
        self.selected_concept_id = None
        self.selected_concept_label = ""
        self.selected_concept_description = ""
        self.student_answer = ""
        self.diagnosis = None
        self.llm_suggested_pattern = ""
        self.diagnosis_validation_errors = []
        self.diagnosis_validation_warnings = []
        self.policy_preview = None
        self.diagnosis_trace = None
        self.running_llm_diagnosis = False

    def load_beta_exercises(self):
        """Load all saved Beta AI exercises."""
        with rx.session() as session:
            self.beta_exercises = list(
                session.exec(
                    select(BetaExercise).order_by(BetaExercise.id.desc())  # type: ignore
                ).all()
            )

    @rx.event
    def select_exercise(self, exercise_id: int | None):
        """Select a Beta AI exercise and load its concepts."""
        if exercise_id is None:
            return

        with rx.session() as session:
            exercise = session.get(BetaExercise, exercise_id)
            if exercise is None:
                return rx.toast.error("Beta AI exercise not found.")

            self.concepts = list(
                session.exec(
                    select(BetaConcept)
                    .where(BetaConcept.beta_exercise_id == exercise_id)
                    .order_by(BetaConcept.order_index)  # type: ignore
                ).all()
            )

        self.selected_exercise_id = exercise_id
        self.selected_exercise_title = exercise.title
        self.selected_concept_id = None
        self.selected_concept_label = ""
        self.selected_concept_description = ""
        self.core_points = []
        self.misconceptions = []
        self.diagnosis = None
        self.llm_suggested_pattern = ""
        self.diagnosis_validation_errors = []
        self.diagnosis_validation_warnings = []
        self.policy_preview = None
        self.diagnosis_trace = None

    @rx.event
    def select_concept(self, concept_id: int | None):
        """Select a concept and load its core points and misconceptions."""
        if concept_id is None:
            return

        with rx.session() as session:
            concept = session.get(BetaConcept, concept_id)
            if concept is None:
                return rx.toast.error("Beta AI concept not found.")

            self.core_points = list(
                session.exec(
                    select(BetaCorePoint)
                    .where(BetaCorePoint.beta_concept_id == concept_id)
                    .order_by(BetaCorePoint.order_index)  # type: ignore
                ).all()
            )
            self.misconceptions = list(
                session.exec(
                    select(BetaMisconception)
                    .where(BetaMisconception.beta_concept_id == concept_id)
                    .order_by(BetaMisconception.order_index)  # type: ignore
                ).all()
            )

        self.selected_concept_id = concept_id
        self.selected_concept_label = concept.label
        self.selected_concept_description = concept.description
        self.diagnosis = None
        self.llm_suggested_pattern = ""
        self.diagnosis_validation_errors = []
        self.diagnosis_validation_warnings = []
        self.policy_preview = None
        self.diagnosis_trace = None

    @rx.event
    def run_mock_diagnosis(self):
        """Run a deterministic mock diagnosis for UI/data-flow testing."""
        if self.selected_concept_id is None:
            return rx.toast.error("Select a concept first.")

        raw_diagnosis = run_mock_diagnosis(
            student_answer=self.student_answer,
            core_points=self.core_points,
        )
        validation_result = validate_and_normalize_diagnosis(
            raw_diagnosis,
            core_points=self.core_points,
            student_answer=self.student_answer,
        )
        self.diagnosis = validation_result.diagnosis
        self.llm_suggested_pattern = validation_result.llm_suggested_pattern
        self.diagnosis_validation_errors = validation_result.errors
        self.diagnosis_validation_warnings = validation_result.warnings
        self.policy_preview = preview_policy_action(
            validation_result.diagnosis,
            concept_label=self.selected_concept_label,
            concept_description=self.selected_concept_description,
            core_points=self.core_points,
            misconceptions=self.misconceptions,
        )
        self.diagnosis_trace = build_diagnosis_trace(
            exercise_title=self.selected_exercise_title,
            concept_label=self.selected_concept_label,
            concept_description=self.selected_concept_description,
            student_answer=self.student_answer,
            diagnosis=self.diagnosis,
            llm_suggested_pattern=self.llm_suggested_pattern,
            validation_errors=self.diagnosis_validation_errors,
            validation_warnings=self.diagnosis_validation_warnings,
            policy_preview=self.policy_preview,
        )

    @rx.event(background=True)
    async def run_llm_diagnosis(self):
        """Run a structured OpenAI diagnosis for the selected concept."""
        async with self:
            if self.selected_concept_id is None:
                yield rx.toast.error("Select a concept first.")
                return
            if not self.student_answer.strip():
                yield rx.toast.error("Enter a student answer first.")
                return
            if self.running_llm_diagnosis:
                return

            self.running_llm_diagnosis = True
            exercise_title = self.selected_exercise_title
            concept_label = self.selected_concept_label
            concept_description = self.selected_concept_description
            core_points = self.core_points
            misconceptions = self.misconceptions
            student_answer = self.student_answer
        yield

        try:
            raw_diagnosis = await run_llm_diagnosis(
                exercise_title=exercise_title,
                concept_label=concept_label,
                concept_description=concept_description,
                core_points=core_points,
                misconceptions=misconceptions,
                student_answer=student_answer,
            )
            validation_result = validate_and_normalize_diagnosis(
                raw_diagnosis,
                core_points=core_points,
                student_answer=student_answer,
            )
        except Exception as exc:
            async with self:
                self.running_llm_diagnosis = False
            yield rx.toast.error(f"LLM diagnosis failed: {exc}")
            return

        async with self:
            self.diagnosis = validation_result.diagnosis
            self.llm_suggested_pattern = validation_result.llm_suggested_pattern
            self.diagnosis_validation_errors = validation_result.errors
            self.diagnosis_validation_warnings = validation_result.warnings
            self.policy_preview = preview_policy_action(
                validation_result.diagnosis,
                concept_label=concept_label,
                concept_description=concept_description,
                core_points=core_points,
                misconceptions=misconceptions,
            )
            self.diagnosis_trace = build_diagnosis_trace(
                exercise_title=exercise_title,
                concept_label=concept_label,
                concept_description=concept_description,
                student_answer=student_answer,
                diagnosis=self.diagnosis,
                llm_suggested_pattern=self.llm_suggested_pattern,
                validation_errors=self.diagnosis_validation_errors,
                validation_warnings=self.diagnosis_validation_warnings,
                policy_preview=self.policy_preview,
            )
            self.running_llm_diagnosis = False
        yield rx.toast.success("LLM diagnosis completed.")
