"""State for the Beta AI chat page."""

from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import col, select

import aitutor.global_vars as gv
from aitutor import routes
from aitutor.auth.protection import state_has_lecture_role, state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.beta_ai.audit import build_diagnosis_trace
from aitutor.beta_ai.diagnosis import (
    DiagnosisResponse,
    validate_and_normalize_diagnosis,
)
from aitutor.beta_ai.diagnosis import (
    run_llm_diagnosis as run_structured_llm_diagnosis,
)
from aitutor.beta_ai.policy import (
    PolicyPreview,
    policy_preview_for_level_repair,
    policy_preview_for_next_level,
    preview_policy_action,
    should_use_level_transition_policy,
)
from aitutor.beta_ai.schemas import OpenAIUsageError
from aitutor.beta_ai.student_state import (
    build_cumulative_evidence_summary,
    normalized_level_status,
    update_student_concept_state_from_diagnosis,
)
from aitutor.beta_ai.tutor_turn import (
    TutorTurnResponse,
    choose_question_level,
    repair_leaky_tutor_turn,
    run_concept_intro_turn_generation,
    run_level_transition_question_generation,
    run_tutor_turn_generation,
    safe_fallback_tutor_turn,
    tutor_turn_reveals_answer,
)
from aitutor.config import get_config
from aitutor.global_vars import TIME_ZONE
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import (
    BetaConcept,
    BetaCorePoint,
    BetaExercise,
    BetaExerciseResult,
    BetaExerciseTraceLog,
    BetaMisconception,
    BetaStudentConceptState,
    GlobalPermission,
    LectureRole,
    Report,
)
from aitutor.utilities.lecture_permissions import (
    get_user_lecture_role,
    user_may_view_lecture,
)


def beta_exercise_is_accessible(
    exercise: BetaExercise,
    lecture_role: LectureRole | None,
    global_permissions: list[GlobalPermission],
) -> bool:
    """Keep hidden and future exercises inaccessible to students."""
    return (
        GlobalPermission.ADMIN in global_permissions
        or (lecture_role is not None and lecture_role >= LectureRole.TUTOR)
        or (not exercise.is_hidden and exercise.is_started)
    )


class BetaAIChatState(SessionState):
    """State for the independent Beta AI chat with first-concept diagnosis.

    This state intentionally does not reuse the regular ChatState or ExerciseResult.
    Beta AI keeps its own conversation, diagnosis traces, and student concept state.
    """

    exercise_title: str = ""
    exercise_description: str = ""
    source_material_filename: str = ""
    current_beta_exercise_id: int | None = None
    current_lecture_id: int | None = None
    current_userinfo_id: int | None = None
    concepts: list[BetaConcept] = []
    current_concept_index: int = 0
    concept_count: int = 0
    all_concepts_completed: bool = False
    selected_concept_id: int | None = None
    selected_concept_label: str = ""
    selected_concept_description: str = ""
    core_points: list[BetaCorePoint] = []
    misconceptions: list[BetaMisconception] = []
    messages: list[dict[str, str]] = []
    student_message: str = ""
    running_diagnosis: bool = False
    last_diagnosis_pattern: str = ""
    last_policy_action: str = ""
    last_policy_rule_id: str = ""
    last_trace_json: str = ""
    last_trace_log_id: int | None = None
    trace_history_count: int = 0
    concept_state: str = "unseen"
    concept_attempts_total: int = 0
    concept_successful_attempts: int = 0
    concept_misconception_hits: int = 0
    active_misconceptions: list[dict] = []
    resolved_misconceptions: list[dict] = []
    cumulative_covered_core_point_ids: list[int] = []
    cumulative_missing_core_point_ids: list[int] = []
    current_question: str = ""
    current_question_level: str = "basic_understanding"
    current_focus_core_point_id: int | None = None
    level_status: dict[str, str] = {}
    completion_unlocked: bool = False
    conversation_is_submitted: bool = False
    analysis_allowed: bool = True
    submit_time_stamp: str = ""
    is_overdue: bool = False
    current_tokens: int = 0
    token_limit: int = 0
    report_text: str = ""

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def set_student_message(self, value: str):
        """Set the current student draft message."""
        self.student_message = value

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def set_report_text(self, value: str):
        """Set the report text and enforce the configured maximum length."""
        self.report_text = value[: gv.REPORT_MAX_LEN]

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def set_analysis_allowed(self, value: bool):
        """Save this student's analysis preference for the current exercise."""
        if not self._has_current_chat_access():
            return
        userinfo = self._authenticated_user_info
        if (
            userinfo is None
            or userinfo.id is None
            or self.current_beta_exercise_id is None
            or self.current_userinfo_id != userinfo.id
        ):
            return
        with rx.session() as session:
            result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaExerciseResult.userinfo_id == userinfo.id,
                )
            ).one_or_none()
            if result is None:
                result = BetaExerciseResult(
                    beta_exercise_id=self.current_beta_exercise_id,
                    userinfo_id=userinfo.id,
                    conversation_text=self.messages,
                    analysis_allowed=value,
                    started_at=datetime.now(ZoneInfo(TIME_ZONE)),
                )
            else:
                result.analysis_allowed = value
            result.updated_at = datetime.now(ZoneInfo(TIME_ZONE))
            session.add(result)
            session.commit()
        self.analysis_allowed = value

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    async def on_load(self):
        """Load the selected visible Beta AI exercise from the route parameter."""
        self._global_load()
        self.reset_chat()
        userinfo = self._authenticated_user_info
        if userinfo is None or userinfo.id is None:
            yield rx.redirect(routes.LOGIN)
            return

        try:
            lecture_id = self._get_route_param_or_error("lecture_id", dtype=int)
            beta_exercise_id = self._get_route_param_or_error(
                "beta_exercise_id", dtype=int
            )
        except KeyError, ValueError, TypeError:
            yield rx.redirect(routes.NOT_FOUND)
            return

        with rx.session() as session:
            self.token_limit = max(1, get_config().exercise_token_limit)
            exercise = session.get(BetaExercise, beta_exercise_id)
            if exercise is None or exercise.lecture_id != lecture_id:
                yield rx.redirect(routes.NOT_FOUND)
                return

            if (
                self.authenticated_user is None
                or self.authenticated_user.id is None
                or not user_may_view_lecture(
                    session,
                    user_id=self.authenticated_user.id,
                    global_permissions=self.global_permissions,
                    lecture_id=lecture_id,
                )
            ):
                yield rx.redirect(routes.MY_LECTURES)
                return

            if not beta_exercise_is_accessible(
                exercise,
                get_user_lecture_role(
                    session,
                    user_id=self.authenticated_user.id,
                    lecture_id=lecture_id,
                ),
                self.global_permissions,
            ):
                yield rx.redirect(routes.NOT_FOUND)
                return

            concepts = list(
                session.exec(
                    select(BetaConcept)
                    .where(BetaConcept.beta_exercise_id == beta_exercise_id)
                    .order_by(col(BetaConcept.order_index))
                ).all()
            )
            concept_states = {
                state.beta_concept_id: state
                for state in session.exec(
                    select(BetaStudentConceptState).where(
                        BetaStudentConceptState.userinfo_id == userinfo.id,
                        BetaStudentConceptState.beta_exercise_id == beta_exercise_id,
                    )
                ).all()
            }
            current_concept_index = self.select_first_incomplete_concept_index(
                concepts, concept_states
            )
            all_concepts_completed = bool(concepts) and all(
                concept.id in concept_states
                and concept_states[concept.id].state == "secure"
                for concept in concepts
                if concept.id is not None
            )
            concept = concepts[current_concept_index] if concepts else None

            core_points: list[BetaCorePoint] = []
            misconceptions: list[BetaMisconception] = []
            conversation_text: list[dict[str, str]] = []
            latest_trace: dict = {}
            trace_history_count = 0
            trace_log_id: int | None = None
            concept_state = "unseen"
            concept_attempts_total = 0
            concept_successful_attempts = 0
            concept_misconception_hits = 0
            active_misconceptions: list[dict] = []
            resolved_misconceptions: list[dict] = []
            cumulative_covered_core_point_ids: list[int] = []
            cumulative_missing_core_point_ids: list[int] = []
            level_status: dict[str, str] = normalized_level_status(None)
            if concept is not None and concept.id is not None:
                core_points = list(
                    session.exec(
                        select(BetaCorePoint)
                        .where(BetaCorePoint.beta_concept_id == concept.id)
                        .order_by(col(BetaCorePoint.order_index))
                    ).all()
                )
                misconceptions = list(
                    session.exec(
                        select(BetaMisconception)
                        .where(BetaMisconception.beta_concept_id == concept.id)
                        .order_by(col(BetaMisconception.order_index))
                    ).all()
                )

            beta_result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id == beta_exercise_id,
                    BetaExerciseResult.userinfo_id == userinfo.id,
                )
            ).one_or_none()
            if beta_result is not None:
                conversation_text = beta_result.conversation_text
                self.load_beta_result_state(beta_result)
                if beta_result.id is not None:
                    trace_logs = list(
                        session.exec(
                            select(BetaExerciseTraceLog)
                            .where(
                                BetaExerciseTraceLog.beta_exercise_result_id
                                == beta_result.id
                            )
                            .order_by(col(BetaExerciseTraceLog.turn_index))
                        ).all()
                    )
                    if trace_logs:
                        latest_trace = trace_logs[-1].trace_entry
                        trace_history_count = len(trace_logs)
                        trace_log_id = trace_logs[-1].id

            if concept is not None and concept.id is not None:
                student_concept_state = concept_states.get(concept.id)
                if student_concept_state is not None:
                    concept_state = student_concept_state.state
                    concept_attempts_total = student_concept_state.attempts_total
                    concept_successful_attempts = (
                        student_concept_state.successful_attempts
                    )
                    concept_misconception_hits = (
                        student_concept_state.misconception_hits
                    )
                    active_misconceptions = (
                        student_concept_state.active_misconceptions or []
                    )
                    resolved_misconceptions = (
                        student_concept_state.resolved_misconceptions or []
                    )
                    cumulative_covered_core_point_ids = (
                        student_concept_state.covered_core_point_ids or []
                    )
                    cumulative_missing_core_point_ids = (
                        student_concept_state.missing_core_point_ids or []
                    )
                    level_status = normalized_level_status(
                        student_concept_state.level_status
                    )

        self.exercise_title = exercise.title
        self.exercise_description = exercise.description
        self.source_material_filename = exercise.source_material_filename
        self.is_overdue = exercise.deadline_exceeded
        self.current_beta_exercise_id = beta_exercise_id
        self.current_lecture_id = exercise.lecture_id
        self.current_userinfo_id = userinfo.id
        self.concepts = concepts
        self.current_concept_index = current_concept_index
        self.concept_count = len(concepts)
        self.all_concepts_completed = all_concepts_completed
        if all_concepts_completed:
            self.completion_unlocked = True
        self.selected_concept_id = concept.id if concept else None
        self.selected_concept_label = concept.label if concept else ""
        self.selected_concept_description = concept.description if concept else ""
        self.core_points = core_points
        self.misconceptions = misconceptions
        self.messages = conversation_text
        self.last_trace_json = trace_log_json(latest_trace) if latest_trace else ""
        self.last_trace_log_id = trace_log_id
        self.trace_history_count = trace_history_count
        self.concept_state = concept_state
        self.concept_attempts_total = concept_attempts_total
        self.concept_successful_attempts = concept_successful_attempts
        self.concept_misconception_hits = concept_misconception_hits
        self.active_misconceptions = active_misconceptions
        self.resolved_misconceptions = resolved_misconceptions
        self.cumulative_covered_core_point_ids = cumulative_covered_core_point_ids
        self.cumulative_missing_core_point_ids = cumulative_missing_core_point_ids
        self.level_status = level_status
        self.restore_current_question_context_from_trace(latest_trace)
        if not conversation_text and not self.token_limit_reached:
            try:
                intro_turn = await self.generate_concept_intro_turn(
                    transition_kind="initial",
                )
                self.append_tutor_turn_message(intro_turn)
                self.save_conversation_to_db(tokens_to_add=intro_turn.tokens_used)
            except OpenAIUsageError as exc:
                self.use_initial_tutor_fallback()
                self.save_conversation_to_db(tokens_to_add=exc.tokens_used)
            except Exception:
                self.use_initial_tutor_fallback()
            self.save_conversation_to_db()
        elif not conversation_text:
            self.use_initial_tutor_fallback()
            self.save_conversation_to_db()

    @rx.var
    def token_limit_reached(self) -> bool:
        """Check whether the exercise token limit has been reached."""
        return self.current_tokens >= self.token_limit

    @rx.var
    def token_warning_threshold_reached(self) -> bool:
        """Check whether the token warning threshold has been reached."""
        return self.current_tokens >= (
            self.token_limit * gv.CHAT_TOKEN_WARNING_THRESHOLD
        )

    @rx.var
    def token_usage_percentage(self) -> int:
        """Return the current token usage as a percentage."""
        if self.token_limit == 0:
            return 0
        return int((self.current_tokens / self.token_limit) * 100)

    @rx.var
    def report_char_count(self) -> int:
        """Return the current report character count."""
        return len(self.report_text)

    @rx.var
    def report_is_valid(self) -> bool:
        """Return whether the report contains valid text."""
        return 0 < len(self.report_text.strip()) <= gv.REPORT_MAX_LEN

    @rx.var
    def can_send_message(self) -> bool:
        """Whether the student can send the current draft message."""
        return bool(
            self.student_message.strip()
            and self.selected_concept_id is not None
            and not self.running_diagnosis
            and not self.token_limit_reached
        )

    @rx.var
    def can_submit_conversation(self) -> bool:
        """Whether the completed conversation is ready for submission."""
        return (
            self.completion_unlocked
            and not self.running_diagnosis
            and not self.is_overdue
        )

    @rx.var
    def has_selected_concept(self) -> bool:
        """Whether this exercise has a concept available for diagnosis."""
        return self.selected_concept_id is not None

    @rx.var
    def concept_progress_label(self) -> str:
        """Return the current concept position for display."""
        if self.concept_count == 0:
            return BT.beta_ai_concept_progress(self.language, 0, 0)
        return BT.beta_ai_concept_progress(
            self.language, self.current_concept_index + 1, self.concept_count
        )

    @rx.var
    def can_go_previous_concept(self) -> bool:
        """Whether manual previous-concept navigation is available."""
        return self.current_concept_index > 0 and not self.running_diagnosis

    @rx.var
    def can_go_next_concept(self) -> bool:
        """Whether manual next-concept navigation is available."""
        return (
            self.concept_count > 0
            and self.current_concept_index < self.concept_count - 1
            and not self.running_diagnosis
        )

    @rx.var
    def concept_summary(self) -> str:
        """Return the current first-concept summary for display."""
        if self.selected_concept_id is None:
            return BT.beta_ai_no_concepts_found(self.language)
        return BT.beta_ai_concept_summary(
            self.language,
            progress=self.concept_progress_label,
            label=self.selected_concept_label,
            core_points=len(self.core_points),
            misconceptions=len(self.misconceptions),
            completed=self.all_concepts_completed,
        )

    @rx.var
    def has_last_trace(self) -> bool:
        """Whether a diagnosis trace preview exists for the latest student turn."""
        return bool(self.last_trace_json)

    @rx.var
    def trace_history_count_label(self) -> str:
        """Return trace history count for display."""
        return BT.beta_ai_trace_entries(self.language, self.trace_history_count)

    @rx.var
    def last_trace_log_id_label(self) -> str:
        """Return latest trace log id for display."""
        if self.last_trace_log_id is None:
            return ""
        return BT.beta_ai_trace_log_id(self.language, self.last_trace_log_id)

    @rx.var
    def concept_state_summary(self) -> str:
        """Return the current student concept state summary for display."""
        return BT.beta_ai_concept_state_summary(
            self.language,
            state=self.concept_state,
            attempts=self.concept_attempts_total,
            successful=self.concept_successful_attempts,
            misconceptions=self.concept_misconception_hits,
        )

    @rx.var
    def cumulative_evidence_summary(self) -> str:
        """Return cumulative core-point evidence summary for display."""
        core_points_by_id = {
            core_point.id: core_point.text
            for core_point in self.core_points
            if core_point.id
        }
        covered_lines = [
            f"✓ {core_points_by_id[core_point_id]}"
            for core_point_id in self.cumulative_covered_core_point_ids
            if core_point_id in core_points_by_id
        ]
        missing_lines = [
            f"• {core_points_by_id[core_point_id]}"
            for core_point_id in self.cumulative_missing_core_point_ids
            if core_point_id in core_points_by_id
        ]

        covered_summary = (
            "\n".join(covered_lines)
            if covered_lines
            else BT.beta_ai_none_yet(self.language)
        )
        missing_summary = (
            "\n".join(missing_lines)
            if missing_lines
            else BT.beta_ai_none(self.language)
        )
        return BT.beta_ai_evidence_summary(
            self.language, covered_summary, missing_summary
        )

    @rx.var
    def level_status_summary(self) -> str:
        """Return reduced Bloom progression status for display."""
        status = normalized_level_status(self.level_status)
        return BT.beta_ai_level_summary(
            self.language,
            status["basic_understanding"],
            status["explain_reasoning"],
            status["apply_or_compare"],
        )

    @rx.var
    def has_trace_log_id(self) -> bool:
        """Whether a persisted trace log id is available."""
        return self.last_trace_log_id is not None

    @rx.var
    def beta_finished_view_url(self) -> str:
        """Return the student's Beta AI finished-view URL for this exercise."""
        if self.current_beta_exercise_id is None or self.current_lecture_id is None:
            return routes.MY_LECTURES
        return (
            f"{routes.BETA_AI_FINISHED_VIEW}/{self.current_lecture_id}"
            f"/{self.current_beta_exercise_id}"
        )

    @rx.var
    def exercises_url(self) -> str:
        """Return the exercise list URL for the current lecture."""
        if self.current_lecture_id is None:
            return routes.MY_LECTURES
        return f"{routes.LECTURE_EXERCISES}/{self.current_lecture_id}"

    @rx.var
    def initial_tutor_message(self) -> str:
        """Return the initial tutor message based on concept availability."""
        if self.selected_concept_id is None:
            return BT.beta_ai_no_concept_registry(self.language)
        return BT.beta_ai_initial_message(
            self.language,
            self.concept_progress_label,
            self.selected_concept_label,
            self.initial_tutor_question,
        )

    @rx.var
    def initial_tutor_question(self) -> str:
        """Return a non-leaking first question for the selected concept."""
        if self.selected_concept_id is None:
            return ""
        return BT.beta_ai_initial_question(self.language, self.selected_concept_label)

    def load_beta_result_state(self, beta_result: BetaExerciseResult) -> None:
        """Restore persisted conversation metadata from a Beta AI result."""
        self.current_tokens = beta_result.tokens_used
        self.analysis_allowed = beta_result.analysis_allowed
        self.completion_unlocked = beta_result.completion_unlocked
        self.conversation_is_submitted = bool(beta_result.submit_time_stamp)
        self.submit_time_stamp = (
            beta_result.submit_time_stamp.isoformat()
            if beta_result.submit_time_stamp
            else ""
        )

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def submit_report(self):
        """Save a Beta AI conversation report with an immutable chat snapshot."""
        if not self._has_current_chat_access():
            return
        if (
            self.current_beta_exercise_id is None
            or self.current_lecture_id is None
            or self.current_userinfo_id is None
            or not self.report_text.strip()
        ):
            return rx.toast.error(
                title=BT.no_report_message_title(self.language),
                description=BT.no_report_message_description(self.language),
                position="bottom-center",
                invert=True,
            )

        with rx.session() as session:
            exercise = session.get(BetaExercise, self.current_beta_exercise_id)
            if exercise is None or exercise.lecture_id != self.current_lecture_id:
                return rx.toast.error(
                    title=BT.no_report_message_title(self.language),
                    description=BT.no_report_message_description(self.language),
                    position="bottom-center",
                    invert=True,
                )

            report = Report(
                beta_exercise_id=exercise.id,
                exercise_type="beta",
                lecture_id=exercise.lecture_id,
                userinfo_id=self.current_userinfo_id,
                report_text=self.report_text.strip(),
                looked_at=False,
                conversation_snapshot=[message.copy() for message in self.messages],
            )
            session.add(report)
            session.commit()

        self.report_text = ""
        return rx.toast.success(
            title=BT.successful_report_title(self.language),
            description=BT.successful_report_description(self.language),
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def reset_chat(self):
        """Reset the in-memory chat skeleton state."""
        self.exercise_title = BT.beta_ai_no_selected_exercise(self.language)
        self.exercise_description = ""
        self.source_material_filename = ""
        self.current_beta_exercise_id = None
        self.current_lecture_id = None
        self.current_userinfo_id = None
        self.concepts = []
        self.current_concept_index = 0
        self.concept_count = 0
        self.all_concepts_completed = False
        self.selected_concept_id = None
        self.selected_concept_label = ""
        self.selected_concept_description = ""
        self.core_points = []
        self.misconceptions = []
        self.messages = []
        self.student_message = ""
        self.running_diagnosis = False
        self.last_diagnosis_pattern = ""
        self.last_policy_action = ""
        self.last_policy_rule_id = ""
        self.last_trace_json = ""
        self.last_trace_log_id = None
        self.trace_history_count = 0
        self.concept_state = "unseen"
        self.concept_attempts_total = 0
        self.concept_successful_attempts = 0
        self.concept_misconception_hits = 0
        self.active_misconceptions = []
        self.resolved_misconceptions = []
        self.cumulative_covered_core_point_ids = []
        self.cumulative_missing_core_point_ids = []
        self.current_question = ""
        self.current_question_level = "basic_understanding"
        self.current_focus_core_point_id = None
        self.level_status = normalized_level_status(None)
        self.completion_unlocked = False
        self.conversation_is_submitted = False
        self.analysis_allowed = True
        self.submit_time_stamp = ""
        self.is_overdue = False
        self.current_tokens = 0
        self.token_limit = 0
        self.report_text = ""

    def fallback_question_for_level(self, question_level: str) -> str:
        """Return a deterministic non-leaking fallback question for a level."""
        if self.selected_concept_id is None:
            return ""
        if question_level == "explain_reasoning":
            return BT.beta_ai_fallback_explain_question(
                self.language, self.selected_concept_label
            )
        if question_level == "apply_or_compare":
            return BT.beta_ai_fallback_apply_question(
                self.language, self.selected_concept_label
            )
        return self.initial_tutor_question

    def use_initial_tutor_fallback(self) -> None:
        """Restore the deterministic initial tutor message and question context."""
        self.messages = [{"role": "tutor", "content": self.initial_tutor_message}]
        self.current_question = self.initial_tutor_question
        self.current_question_level = "basic_understanding"
        self.current_focus_core_point_id = None

    @staticmethod
    def tokens_used_from_exception(exc: Exception) -> int:
        """Return OpenAI usage attached to an exception, if available."""
        return exc.tokens_used if isinstance(exc, OpenAIUsageError) else 0

    async def generate_concept_intro_turn(
        self,
        *,
        previous_concept_label: str = "",
        transition_kind: str = "initial",
    ):
        """Generate a natural first tutor turn for the current concept."""
        intro_turn = await run_concept_intro_turn_generation(
            exercise_title=self.exercise_title,
            concept_label=self.selected_concept_label,
            concept_description=self.selected_concept_description,
            core_points=self.core_points,
            misconceptions=self.misconceptions,
            previous_concept_label=previous_concept_label,
            transition_kind=transition_kind,  # type: ignore[arg-type]
        )
        if tutor_turn_reveals_answer(intro_turn, core_points=self.core_points):
            raise OpenAIUsageError(
                "Generated concept intro revealed expected answer wording.",
                tokens_used=intro_turn.tokens_used,
            )
        return intro_turn

    def append_tutor_turn_message(self, tutor_turn: TutorTurnResponse) -> None:
        """Append a generated tutor turn and update current-question state."""
        tutor_response = (
            f"{tutor_turn.feedback_brief}\n\n"
            f"{BT.beta_ai_question_prefix(self.language)}{tutor_turn.next_question}"
        )
        self.messages.append({"role": "tutor", "content": tutor_response})
        self.current_question = tutor_turn.next_question
        self.current_question_level = tutor_turn.question_level
        self.current_focus_core_point_id = tutor_turn.focus_core_point_id

    def restore_current_question_context_from_trace(self, latest_trace: dict) -> None:
        """Restore current tutor-question context after page/state reload.

        Conversation text is persisted, but Reflex state fields are not. Without
        this reconstruction, the chat can visually show an explain/apply question
        while the internal state falls back to the initial basic question.
        """
        generated_turn = latest_trace.get("generated_tutor_turn", {})
        restored_question = generated_turn.get("next_question")
        restored_level = generated_turn.get("question_level")
        restored_focus_id = generated_turn.get("focus_core_point_id")

        if restored_question and restored_level:
            self.current_question = str(restored_question)
            self.current_question_level = str(restored_level)
            self.current_focus_core_point_id = restored_focus_id
            return

        status = normalized_level_status(self.level_status)
        if status["basic_understanding"] != "passed":
            fallback_level = "basic_understanding"
        elif status["explain_reasoning"] != "passed":
            fallback_level = "explain_reasoning"
        else:
            fallback_level = "apply_or_compare"

        self.current_question_level = fallback_level
        self.current_question = self.fallback_question_for_level(fallback_level)
        self.current_focus_core_point_id = (
            self.core_points[0].id
            if self.core_points and self.core_points[0].id
            else None
        )

    def select_first_incomplete_concept_index(
        self,
        concepts: list[BetaConcept],
        concept_states: dict[int, BetaStudentConceptState],
    ) -> int:
        """Return the first concept whose student state is not secure."""
        for index, concept in enumerate(concepts):
            assert concept.id is not None, "Persisted Beta AI concept has no ID."
            student_state = concept_states.get(concept.id)
            if student_state is None or student_state.state != "secure":
                return index
        return max(len(concepts) - 1, 0)

    def load_concept_context(self, concept_index: int) -> bool:
        """Load selected concept, registry entries, and student state by index."""
        if (
            self.current_beta_exercise_id is None
            or self.current_userinfo_id is None
            or not self.concepts
            or concept_index < 0
            or concept_index >= len(self.concepts)
        ):
            return False

        concept = self.concepts[concept_index]
        assert concept.id is not None, "Persisted Beta AI concept has no ID."

        with rx.session() as session:
            persisted_concept = session.get(BetaConcept, concept.id)
            if persisted_concept is None:
                return False
            core_points = list(
                session.exec(
                    select(BetaCorePoint)
                    .where(BetaCorePoint.beta_concept_id == persisted_concept.id)
                    .order_by(col(BetaCorePoint.order_index))
                ).all()
            )
            misconceptions = list(
                session.exec(
                    select(BetaMisconception)
                    .where(BetaMisconception.beta_concept_id == persisted_concept.id)
                    .order_by(col(BetaMisconception.order_index))
                ).all()
            )
            student_concept_state = session.exec(
                select(BetaStudentConceptState).where(
                    BetaStudentConceptState.userinfo_id == self.current_userinfo_id,
                    BetaStudentConceptState.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaStudentConceptState.beta_concept_id == persisted_concept.id,
                )
            ).one_or_none()

        self.current_concept_index = concept_index
        self.selected_concept_id = persisted_concept.id
        self.selected_concept_label = persisted_concept.label
        self.selected_concept_description = persisted_concept.description
        self.core_points = core_points
        self.misconceptions = misconceptions
        self.current_question_level = "basic_understanding"
        self.current_focus_core_point_id = (
            core_points[0].id if core_points and core_points[0].id else None
        )

        if student_concept_state is None:
            self.concept_state = "unseen"
            self.concept_attempts_total = 0
            self.concept_successful_attempts = 0
            self.concept_misconception_hits = 0
            self.active_misconceptions = []
            self.resolved_misconceptions = []
            self.cumulative_covered_core_point_ids = []
            self.cumulative_missing_core_point_ids = []
            self.level_status = normalized_level_status(None)
        else:
            self.concept_state = student_concept_state.state
            self.concept_attempts_total = student_concept_state.attempts_total
            self.concept_successful_attempts = student_concept_state.successful_attempts
            self.concept_misconception_hits = student_concept_state.misconception_hits
            self.active_misconceptions = (
                student_concept_state.active_misconceptions or []
            )
            self.resolved_misconceptions = (
                student_concept_state.resolved_misconceptions or []
            )
            self.cumulative_covered_core_point_ids = (
                student_concept_state.covered_core_point_ids or []
            )
            self.cumulative_missing_core_point_ids = (
                student_concept_state.missing_core_point_ids or []
            )
            self.level_status = normalized_level_status(
                student_concept_state.level_status
            )

        self.current_question = self.initial_tutor_question
        self.all_concepts_completed = self.are_all_concepts_secure()
        return True

    def are_all_concepts_secure(self) -> bool:
        """Return whether all concepts in the current exercise are secure."""
        if (
            self.current_beta_exercise_id is None
            or self.current_userinfo_id is None
            or not self.concepts
        ):
            return False
        concept_ids = [
            concept.id for concept in self.concepts if concept.id is not None
        ]
        if not concept_ids:
            return False
        with rx.session() as session:
            secure_count = len(
                session.exec(
                    select(BetaStudentConceptState).where(
                        BetaStudentConceptState.userinfo_id == self.current_userinfo_id,
                        BetaStudentConceptState.beta_exercise_id
                        == self.current_beta_exercise_id,
                        BetaStudentConceptState.beta_concept_id.in_(concept_ids),  # type: ignore[attr-defined]
                        BetaStudentConceptState.state == "secure",
                    )
                ).all()
            )
        return secure_count == len(concept_ids)

    def append_concept_transition_message(
        self, *, previous_label: str, automatic: bool
    ) -> None:
        """Append a deterministic concept-transition tutor message."""
        self.messages.append(
            {
                "role": "tutor",
                "content": BT.beta_ai_transition(
                    self.language,
                    previous=previous_label,
                    progress=self.concept_progress_label,
                    label=self.selected_concept_label,
                    question=self.current_question,
                    automatic=automatic,
                ),
            }
        )

    def append_all_concepts_completed_message(self) -> None:
        """Append a deterministic message when the full concept sequence is secure."""
        self.messages.append(
            {
                "role": "tutor",
                "content": BT.beta_ai_all_concepts_completed(self.language),
            }
        )
        self.completion_unlocked = True

    def persist_completion_unlocked(self) -> None:
        """Persist that the student unlocked Beta AI submission for this exercise."""
        if self.current_beta_exercise_id is None or self.current_userinfo_id is None:
            return

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            beta_result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaExerciseResult.userinfo_id == self.current_userinfo_id,
                )
            ).one_or_none()
            if beta_result is None:
                beta_result = BetaExerciseResult(
                    beta_exercise_id=self.current_beta_exercise_id,
                    userinfo_id=self.current_userinfo_id,
                    conversation_text=self.messages,
                    completion_unlocked=True,
                    completed_at=now,
                    started_at=now,
                    updated_at=now,
                )
                session.add(beta_result)
            else:
                beta_result.conversation_text = self.messages
                beta_result.completion_unlocked = True
                if beta_result.completed_at is None:
                    beta_result.completed_at = now
                beta_result.updated_at = now
            session.commit()

    def advance_to_next_incomplete_concept(self) -> dict[str, object]:
        """Automatically move to the next non-secure concept if available."""
        previous_concept_id = self.selected_concept_id
        previous_label = self.selected_concept_label
        for next_index in range(self.current_concept_index + 1, len(self.concepts)):
            concept = self.concepts[next_index]
            assert concept.id is not None, "Persisted Beta AI concept has no ID."
            with rx.session() as session:
                student_state = session.exec(
                    select(BetaStudentConceptState).where(
                        BetaStudentConceptState.userinfo_id == self.current_userinfo_id,
                        BetaStudentConceptState.beta_exercise_id
                        == self.current_beta_exercise_id,
                        BetaStudentConceptState.beta_concept_id == concept.id,
                    )
                ).one_or_none()
            if (student_state is None or student_state.state != "secure") and (
                self.load_concept_context(next_index)
            ):
                return {
                    "advanced": True,
                    "completed_all": False,
                    "from_concept_id": previous_concept_id,
                    "to_concept_id": self.selected_concept_id,
                    "previous_label": previous_label,
                    "reason": "current_concept_secure",
                }

        self.all_concepts_completed = self.are_all_concepts_secure()
        if self.all_concepts_completed:
            self.append_all_concepts_completed_message()
            self.persist_completion_unlocked()
            return {
                "advanced": False,
                "completed_all": True,
                "from_concept_id": previous_concept_id,
                "to_concept_id": None,
                "previous_label": previous_label,
                "reason": "all_concepts_secure",
            }
        return {"advanced": False, "completed_all": False, "reason": "no_next_concept"}

    def _navigate_to_concept(self, offset: int) -> None:
        """Navigate manually and persist the transition when loading succeeds."""
        previous_label = self.selected_concept_label
        if self.load_concept_context(self.current_concept_index + offset):
            self.append_concept_transition_message(
                previous_label=previous_label,
                automatic=False,
            )
            self.save_conversation_to_db()

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def go_to_previous_concept(self):
        """Manual previous-concept navigation for development/testing."""
        if not self._has_current_chat_access():
            return
        if not self.can_go_previous_concept:
            return
        self._navigate_to_concept(-1)

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def go_to_next_concept(self):
        """Manual next-concept navigation for development/testing."""
        if not self._has_current_chat_access():
            return
        if not self.can_go_next_concept:
            return
        self._navigate_to_concept(1)

    def _has_current_chat_access(self) -> bool:
        """Reject stale chat state and recheck lecture and exercise visibility."""
        if not state_has_lecture_role(self, LectureRole.STUDENT):
            return False
        user = self.authenticated_user
        if user is None or user.id is None:
            return False
        try:
            lecture_id = self._get_route_param_or_error("lecture_id", dtype=int)
            exercise_id = self._get_route_param_or_error("beta_exercise_id", dtype=int)
        except KeyError, ValueError, TypeError:
            return False
        userinfo = self._authenticated_user_info
        if (
            userinfo is None
            or userinfo.id is None
            or self.current_userinfo_id != userinfo.id
            or self.current_lecture_id != lecture_id
            or self.current_beta_exercise_id != exercise_id
        ):
            return False
        with rx.session() as session:
            exercise = session.get(BetaExercise, exercise_id)
            return (
                exercise is not None
                and exercise.lecture_id == lecture_id
                and beta_exercise_is_accessible(
                    exercise,
                    get_user_lecture_role(
                        session,
                        user_id=user.id,
                        lecture_id=lecture_id,
                    ),
                    self.global_permissions,
                )
            )

    def save_conversation_to_db(self, tokens_to_add: int = 0) -> int | None:
        """Persist the Beta AI conversation and accumulate newly consumed tokens."""
        if self.current_beta_exercise_id is None or self.current_userinfo_id is None:
            return None

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            beta_result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaExerciseResult.userinfo_id == self.current_userinfo_id,
                )
            ).one_or_none()

            if beta_result is None:
                beta_result = BetaExerciseResult(
                    beta_exercise_id=self.current_beta_exercise_id,
                    userinfo_id=self.current_userinfo_id,
                    conversation_text=self.messages,
                    completion_unlocked=self.completion_unlocked,
                    tokens_used=tokens_to_add,
                    started_at=now,
                    updated_at=now,
                )
                session.add(beta_result)
                session.flush()
            else:
                beta_result.conversation_text = self.messages
                beta_result.completion_unlocked = (
                    beta_result.completion_unlocked or self.completion_unlocked
                )
                if self.completion_unlocked and beta_result.completed_at is None:
                    beta_result.completed_at = now
                beta_result.tokens_used += tokens_to_add
                beta_result.updated_at = now

            session.commit()
            self.current_tokens = beta_result.tokens_used
            return beta_result.id

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def submit_beta_conversation(self):
        """Submit the completed Beta AI conversation for tutor review."""
        if self.running_diagnosis or not self._has_current_chat_access():
            return
        if (
            not self.completion_unlocked
            or self.current_beta_exercise_id is None
            or self.current_userinfo_id is None
        ):
            return rx.toast.error(
                description=BT.beta_ai_complete_before_submit(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            exercise = session.get(BetaExercise, self.current_beta_exercise_id)
            if exercise is None:
                return
            self.is_overdue = exercise.deadline_exceeded
            if self.is_overdue:
                return
            beta_result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaExerciseResult.userinfo_id == self.current_userinfo_id,
                )
            ).one_or_none()
            if beta_result is None:
                beta_result = BetaExerciseResult(
                    beta_exercise_id=self.current_beta_exercise_id,
                    userinfo_id=self.current_userinfo_id,
                    conversation_text=self.messages,
                    started_at=now,
                )
                session.add(beta_result)

            beta_result.conversation_text = self.messages
            beta_result.finished_conversation = self.messages
            beta_result.completion_unlocked = True
            if beta_result.completed_at is None:
                beta_result.completed_at = now
            beta_result.submit_time_stamp = now
            beta_result.updated_at = now
            session.commit()

        self.conversation_is_submitted = True
        self.submit_time_stamp = now.isoformat()
        return rx.toast.success(
            description=BT.beta_ai_submitted(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    def append_trace_to_db(
        self,
        *,
        beta_exercise_result_id: int,
        beta_concept_id: int | None,
        trace_entry: dict,
    ) -> tuple[int | None, int]:
        """Append one per-turn diagnosis trace row."""
        if self.current_beta_exercise_id is None or self.current_userinfo_id is None:
            return None, self.trace_history_count

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            existing_logs = list(
                session.exec(
                    select(BetaExerciseTraceLog)
                    .where(
                        BetaExerciseTraceLog.beta_exercise_result_id
                        == beta_exercise_result_id
                    )
                    .order_by(col(BetaExerciseTraceLog.turn_index))
                ).all()
            )
            next_turn_index = (
                max((log.turn_index for log in existing_logs), default=0) + 1
            )
            trace_entry["turn_index"] = next_turn_index
            trace_entry["created_at"] = now.isoformat()

            trace_log = BetaExerciseTraceLog(
                beta_exercise_result_id=beta_exercise_result_id,
                beta_exercise_id=self.current_beta_exercise_id,
                userinfo_id=self.current_userinfo_id,
                beta_concept_id=beta_concept_id,
                turn_index=next_turn_index,
                concept_label=str(trace_entry.get("concept_label", "")),
                student_answer=str(trace_entry.get("student_answer", "")),
                final_pattern=str(trace_entry.get("final_pattern", "")),
                selected_action=str(trace_entry.get("selected_action", "")),
                selected_rule_id=str(trace_entry.get("selected_rule_id", "")),
                question_level=str(trace_entry.get("current_question_level", "")),
                trace_entry=trace_entry,
                created_at=now,
            )
            session.add(trace_log)
            session.flush()

            session.commit()
            return trace_log.id, next_turn_index

    def _save_conversation_and_trace(
        self, trace_entry: dict, *, beta_concept_id: int | None
    ) -> None:
        """Save the chat and append its trace only when the chat has a result id."""
        beta_exercise_result_id = self.save_conversation_to_db()
        if beta_exercise_result_id is not None:
            trace_log_id, trace_history_count = self.append_trace_to_db(
                beta_exercise_result_id=beta_exercise_result_id,
                beta_concept_id=beta_concept_id,
                trace_entry=trace_entry,
            )
            self.last_trace_log_id = trace_log_id
            self.trace_history_count = trace_history_count

    def build_cumulative_diagnosis(
        self, *, latest_diagnosis: DiagnosisResponse, student_answer: str
    ) -> DiagnosisResponse:
        """Update cumulative evidence and return a cumulative diagnosis view."""
        if (
            self.current_userinfo_id is None
            or self.current_beta_exercise_id is None
            or self.selected_concept_id is None
        ):
            return latest_diagnosis

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            student_state = session.exec(
                select(BetaStudentConceptState).where(
                    BetaStudentConceptState.userinfo_id == self.current_userinfo_id,
                    BetaStudentConceptState.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaStudentConceptState.beta_concept_id == self.selected_concept_id,
                )
            ).one_or_none()

            if student_state is None:
                student_state = BetaStudentConceptState(
                    userinfo_id=self.current_userinfo_id,
                    beta_exercise_id=self.current_beta_exercise_id,
                    beta_concept_id=self.selected_concept_id,
                    state="unseen",
                )
                session.add(student_state)
                session.flush()

            trace_reference = self.trace_history_count + 1
            cumulative_diagnosis = update_student_concept_state_from_diagnosis(
                student_state=student_state,
                latest_diagnosis=latest_diagnosis,
                core_points=self.core_points,
                student_answer=student_answer,
                trace_reference=trace_reference,
                now=now,
                question_level=self.current_question_level,  # type: ignore[arg-type]
            )

            session.commit()

            self.concept_state = student_state.state
            self.concept_attempts_total = student_state.attempts_total
            self.concept_successful_attempts = student_state.successful_attempts
            self.concept_misconception_hits = student_state.misconception_hits
            self.active_misconceptions = student_state.active_misconceptions or []
            self.resolved_misconceptions = student_state.resolved_misconceptions or []
            self.cumulative_covered_core_point_ids = (
                cumulative_diagnosis.covered_core_point_ids
            )
            self.cumulative_missing_core_point_ids = (
                cumulative_diagnosis.missing_core_point_ids
            )
            self.level_status = normalized_level_status(student_state.level_status)

            return cumulative_diagnosis

    def save_last_policy_action_to_student_state(self, policy_action: str) -> None:
        """Persist the latest policy action after policy selection.

        The policy action is computed from the cumulative diagnosis, so it is
        available only after the main student-state update. Keeping this small
        persistence step separate avoids a larger flow rewrite while ensuring the
        StudentConceptState stores both the latest diagnosis and didactic action.
        """
        if (
            self.current_userinfo_id is None
            or self.current_beta_exercise_id is None
            or self.selected_concept_id is None
        ):
            return

        now = datetime.now(ZoneInfo(TIME_ZONE))
        with rx.session() as session:
            student_state = session.exec(
                select(BetaStudentConceptState).where(
                    BetaStudentConceptState.userinfo_id == self.current_userinfo_id,
                    BetaStudentConceptState.beta_exercise_id
                    == self.current_beta_exercise_id,
                    BetaStudentConceptState.beta_concept_id == self.selected_concept_id,
                )
            ).one_or_none()
            if student_state is None:
                return
            student_state.last_policy_action = policy_action
            student_state.updated_at = now
            session.commit()

    def _finish_with_processing_error(self) -> None:
        """Stop processing and show the generic failure message in the chat."""
        self.running_diagnosis = False
        self.messages.append(
            {
                "role": "tutor",
                "content": BT.beta_ai_generic_processing_error(self.language),
            }
        )

    @rx.event(background=True)
    async def send_message(self):
        """Diagnose a student message and append a policy-based tutor response."""
        async with self:
            if not self._has_current_chat_access():
                return
            message = self.student_message.strip()
            if not message:
                return
            if self.token_limit_reached:
                return
            if self.selected_concept_id is None:
                yield rx.toast.error(
                    description=BT.beta_ai_no_concept_registry(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
                return
            if self.running_diagnosis:
                return

            self.running_diagnosis = True
            self.student_message = ""
            self.messages.append({"role": "student", "content": message})

            exercise_title = self.exercise_title
            concept_label = self.selected_concept_label
            concept_id = self.selected_concept_id
            concept_description = self.selected_concept_description
            core_points = self.core_points
            misconceptions = self.misconceptions
            conversation_context = list(self.messages)
            current_question = self.current_question
            current_question_level = self.current_question_level
            current_focus_core_point_id = self.current_focus_core_point_id
            previous_level_status = dict(self.level_status)
            cumulative_evidence_summary = build_cumulative_evidence_summary(
                core_points=core_points,
                covered_core_point_ids=self.cumulative_covered_core_point_ids,
                missing_core_point_ids=self.cumulative_missing_core_point_ids,
            )
        yield

        try:
            raw_diagnosis = await run_structured_llm_diagnosis(
                exercise_title=exercise_title,
                concept_label=concept_label,
                concept_description=concept_description,
                core_points=core_points,
                misconceptions=misconceptions,
                student_answer=message,
                conversation_context=conversation_context,
                cumulative_evidence_summary=cumulative_evidence_summary,
                current_question=current_question,
                current_question_level=current_question_level,
                current_focus_core_point_id=current_focus_core_point_id,
            )
            async with self:
                self.save_conversation_to_db(tokens_to_add=raw_diagnosis.tokens_used)
            validation_result = validate_and_normalize_diagnosis(
                raw_diagnosis,
                core_points=core_points,
                student_answer=message,
                conversation_context=conversation_context,
            )
        except Exception as exc:
            async with self:
                self.save_conversation_to_db(
                    tokens_to_add=self.tokens_used_from_exception(exc)
                )
                self._finish_with_processing_error()
            yield rx.toast.error(
                description=BT.beta_ai_processing_failed(
                    self.language, "diagnosis", exc
                ),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        try:
            async with self:
                cumulative_diagnosis = self.build_cumulative_diagnosis(
                    latest_diagnosis=validation_result.diagnosis,
                    student_answer=message,
                )
        except Exception as exc:
            async with self:
                self._finish_with_processing_error()
            yield rx.toast.error(
                description=BT.beta_ai_processing_failed(
                    self.language, "student_state", exc
                ),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return

        try:
            policy_preview = preview_policy_action(
                cumulative_diagnosis,
                concept_label=concept_label,
                concept_description=concept_description,
                core_points=core_points,
                misconceptions=misconceptions,
            )
        except Exception as exc:
            async with self:
                self._finish_with_processing_error()
            yield rx.toast.error(
                description=BT.beta_ai_processing_failed(self.language, "policy", exc),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if self.concept_state == "secure":
            async with self:
                completed_level_status = dict(self.level_status)
                completed_concept_state = self.concept_state
                completed_active_misconceptions = list(self.active_misconceptions)
                completed_resolved_misconceptions = list(self.resolved_misconceptions)
                completion_policy_preview = PolicyPreview(
                    rule_id="R-CONCEPT-SECURE-01",
                    action="advance_to_next_concept",
                    rationale=(
                        "The current concept has passed basic understanding, "
                        "explain reasoning, and apply/compare. The next didactic "
                        "step is to advance to the next incomplete concept."
                    ),
                    feedback_brief=(
                        f"The student has completed '{concept_label}' across the "
                        "required levels."
                    ),
                    suggested_prompt="Advance to the next concept.",
                )
                self.save_last_policy_action_to_student_state(
                    completion_policy_preview.action
                )
                concept_transition = self.advance_to_next_incomplete_concept()

            if concept_transition.get("advanced"):
                previous_label = str(
                    concept_transition.get("previous_label") or concept_label
                )
                try:
                    transition_turn = await self.generate_concept_intro_turn(
                        previous_concept_label=previous_label,
                        transition_kind="automatic",
                    )
                    async with self:
                        self.save_conversation_to_db(
                            tokens_to_add=transition_turn.tokens_used
                        )
                        self.append_tutor_turn_message(transition_turn)
                except OpenAIUsageError as exc:
                    async with self:
                        self.save_conversation_to_db(tokens_to_add=exc.tokens_used)
                        self.append_concept_transition_message(
                            previous_label=previous_label,
                            automatic=True,
                        )
                except Exception:
                    async with self:
                        self.append_concept_transition_message(
                            previous_label=previous_label,
                            automatic=True,
                        )

            try:
                async with self:
                    trace = build_diagnosis_trace(
                        exercise_title=exercise_title,
                        concept_label=concept_label,
                        concept_description=concept_description,
                        student_answer=message,
                        diagnosis=cumulative_diagnosis,
                        llm_suggested_pattern=validation_result.llm_suggested_pattern,
                        validation_errors=validation_result.errors,
                        validation_warnings=validation_result.warnings,
                        policy_preview=completion_policy_preview,
                    )
                    trace_entry = trace.model_dump()
                    trace_entry["latest_turn_diagnosis"] = (
                        validation_result.diagnosis.model_dump()
                    )
                    trace_entry["cumulative_diagnosis"] = (
                        cumulative_diagnosis.model_dump()
                    )
                    trace_entry["cumulative_covered_core_point_ids"] = (
                        cumulative_diagnosis.covered_core_point_ids
                    )
                    trace_entry["cumulative_missing_core_point_ids"] = (
                        cumulative_diagnosis.missing_core_point_ids
                    )
                    trace_entry["policy_based_on"] = "cumulative_concept_evidence"
                    trace_entry["current_question"] = current_question
                    trace_entry["current_question_level"] = current_question_level
                    trace_entry["current_focus_core_point_id"] = (
                        current_focus_core_point_id
                    )
                    trace_entry["concept_transition"] = concept_transition
                    trace_entry["level_status"] = completed_level_status
                    trace_entry["active_misconceptions"] = (
                        completed_active_misconceptions
                    )
                    trace_entry["resolved_misconceptions"] = (
                        completed_resolved_misconceptions
                    )
                    trace_entry["completed_concept_state"] = completed_concept_state
                    trace_entry["next_concept_level_status"] = self.level_status

                    self.last_diagnosis_pattern = cumulative_diagnosis.diagnosis_pattern
                    self.last_policy_action = completion_policy_preview.action
                    self.last_policy_rule_id = completion_policy_preview.rule_id
                    self.last_trace_json = trace_log_json(trace_entry)
                    self._save_conversation_and_trace(
                        trace_entry, beta_concept_id=concept_id
                    )
                    self.running_diagnosis = False
                return
            except Exception as exc:
                async with self:
                    self._finish_with_processing_error()
                yield rx.toast.error(
                    description=BT.beta_ai_processing_failed(
                        self.language, "completion", exc
                    ),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )
                return
        async with self:
            self.save_last_policy_action_to_student_state(policy_preview.action)
        try:
            next_question_level = choose_question_level(
                cumulative_diagnosis,
                self.level_status,
                current_question_level=current_question_level,  # type: ignore[arg-type]
            )
            use_level_transition_policy = should_use_level_transition_policy(
                previous_level_status=previous_level_status,
                current_level_status=self.level_status,
                current_question_level=current_question_level,
                next_question_level=next_question_level,
            )
            level_transition_policy_preview = (
                policy_preview_for_next_level(
                    concept_label=concept_label,
                    concept_description=concept_description,
                    next_question_level=next_question_level,
                )
                if use_level_transition_policy
                else None
            )
            level_repair_policy_preview = (
                None
                if level_transition_policy_preview is not None
                else policy_preview_for_level_repair(
                    diagnosis=cumulative_diagnosis,
                    concept_label=concept_label,
                    concept_description=concept_description,
                    question_level=current_question_level,
                )
            )
        except Exception as exc:
            async with self:
                self._finish_with_processing_error()
            yield rx.toast.error(
                description=BT.beta_ai_processing_failed(
                    self.language, "question_level", exc
                ),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if level_repair_policy_preview is not None:
            policy_preview = level_repair_policy_preview
            async with self:
                self.save_last_policy_action_to_student_state(policy_preview.action)
        elif level_transition_policy_preview is not None:
            policy_preview = level_transition_policy_preview
            async with self:
                self.save_last_policy_action_to_student_state(policy_preview.action)
        try:
            if level_transition_policy_preview is not None:
                tutor_turn = await run_level_transition_question_generation(
                    concept_label=concept_label,
                    concept_description=concept_description,
                    core_points=core_points,
                    policy_preview=policy_preview,
                    next_question_level=next_question_level,
                    cumulative_evidence_summary=cumulative_evidence_summary,
                    current_question=current_question,
                    student_answer=message,
                )
            else:
                tutor_turn = await run_tutor_turn_generation(
                    concept_label=concept_label,
                    concept_description=concept_description,
                    core_points=core_points,
                    misconceptions=misconceptions,
                    diagnosis=cumulative_diagnosis,
                    policy_preview=policy_preview,
                    question_level=next_question_level,
                    cumulative_evidence_summary=cumulative_evidence_summary,
                    current_question=current_question,
                    student_answer=message,
                )
            async with self:
                self.save_conversation_to_db(tokens_to_add=tutor_turn.tokens_used)
            if tutor_turn_reveals_answer(tutor_turn, core_points=core_points):
                try:
                    repaired_turn = await repair_leaky_tutor_turn(
                        concept_label=concept_label,
                        concept_description=concept_description,
                        core_points=core_points,
                        policy_preview=policy_preview,
                        leaky_tutor_turn=tutor_turn,
                        question_level=next_question_level,
                    )
                    async with self:
                        self.save_conversation_to_db(
                            tokens_to_add=repaired_turn.tokens_used
                        )
                    if tutor_turn_reveals_answer(
                        repaired_turn, core_points=core_points
                    ):
                        tutor_turn = safe_fallback_tutor_turn(
                            diagnosis=cumulative_diagnosis,
                            policy_preview=policy_preview,
                            question_level=next_question_level,
                        )
                    else:
                        tutor_turn = repaired_turn
                except Exception as exc:
                    async with self:
                        self.save_conversation_to_db(
                            tokens_to_add=self.tokens_used_from_exception(exc)
                        )
                    tutor_turn = safe_fallback_tutor_turn(
                        diagnosis=cumulative_diagnosis,
                        policy_preview=policy_preview,
                        question_level=next_question_level,
                    )
        except Exception as exc:
            async with self:
                self.save_conversation_to_db(
                    tokens_to_add=self.tokens_used_from_exception(exc)
                )
            tutor_turn = safe_fallback_tutor_turn(
                diagnosis=cumulative_diagnosis,
                policy_preview=policy_preview,
                question_level=next_question_level,
            )
        try:
            trace = build_diagnosis_trace(
                exercise_title=exercise_title,
                concept_label=concept_label,
                concept_description=concept_description,
                student_answer=message,
                diagnosis=cumulative_diagnosis,
                llm_suggested_pattern=validation_result.llm_suggested_pattern,
                validation_errors=validation_result.errors,
                validation_warnings=validation_result.warnings,
                policy_preview=policy_preview,
            )
            trace_entry = trace.model_dump()
            trace_entry["latest_turn_diagnosis"] = (
                validation_result.diagnosis.model_dump()
            )
            trace_entry["cumulative_diagnosis"] = cumulative_diagnosis.model_dump()
            trace_entry["cumulative_covered_core_point_ids"] = (
                cumulative_diagnosis.covered_core_point_ids
            )
            trace_entry["cumulative_missing_core_point_ids"] = (
                cumulative_diagnosis.missing_core_point_ids
            )
            trace_entry["policy_based_on"] = "cumulative_concept_evidence"
            trace_entry["current_question"] = current_question
            trace_entry["current_question_level"] = current_question_level
            trace_entry["current_focus_core_point_id"] = current_focus_core_point_id
            trace_entry["generated_tutor_turn"] = tutor_turn.model_dump()
            trace_entry["level_status"] = self.level_status
            trace_entry["active_misconceptions"] = self.active_misconceptions
            trace_entry["resolved_misconceptions"] = self.resolved_misconceptions

            async with self:
                self.append_tutor_turn_message(tutor_turn)
                self.last_diagnosis_pattern = cumulative_diagnosis.diagnosis_pattern
                self.last_policy_action = policy_preview.action
                self.last_policy_rule_id = policy_preview.rule_id
                self.last_trace_json = trace_log_json(trace_entry)
                self._save_conversation_and_trace(
                    trace_entry, beta_concept_id=concept_id
                )
                self.running_diagnosis = False
        except Exception as exc:
            async with self:
                self._finish_with_processing_error()
            yield rx.toast.error(
                description=BT.beta_ai_processing_failed(
                    self.language, "tutor_response", exc
                ),
                duration=5000,
                position="bottom-center",
                invert=True,
            )


def trace_log_json(trace: dict) -> str:
    """Return a deterministic JSON string for a persisted latest trace dict."""
    import json

    return json.dumps(trace, indent=2, ensure_ascii=False)
