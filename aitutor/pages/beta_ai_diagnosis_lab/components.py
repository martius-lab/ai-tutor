"""Components for the Beta AI diagnosis lab skeleton."""

import reflex as rx

from aitutor.models import BetaConcept, BetaCorePoint, BetaExercise, BetaMisconception
from aitutor.pages.beta_ai_diagnosis_lab.state import BetaAIDiagnosisLabState


def diagnosis_lab_header() -> rx.Component:
    """Render the diagnosis lab header."""
    return rx.vstack(
        rx.heading("Beta AI Diagnosis Lab", size="7"),
        rx.text(
            "Checkpoint 3: inspect saved concept data and run structured LLM "
            "diagnosis against the selected concept's core points.",
            color_scheme="gray",
        ),
        align="start",
        spacing="1",
        width="100%",
    )


def exercise_row(exercise: BetaExercise) -> rx.Component:
    """Render one selectable exercise row."""
    return rx.table.row(
        rx.table.cell(exercise.title),
        rx.table.cell(exercise.description, max_width="30em"),
        rx.table.cell(
            rx.button(
                "Select",
                size="2",
                on_click=BetaAIDiagnosisLabState.select_exercise(exercise.id),
                _hover={"cursor": "pointer"},
            )
        ),
    )


def exercise_selection_card() -> rx.Component:
    """Render saved exercise selection."""
    return rx.card(
        rx.vstack(
            rx.heading("1. Select Beta AI Exercise", size="4"),
            rx.cond(
                BetaAIDiagnosisLabState.beta_exercises.length() == 0,  # type: ignore
                rx.callout(
                    "No Beta AI exercises saved yet. Create one in Beta AI "
                    "Exercises first.",
                    icon="info",
                    width="100%",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Title"),
                            rx.table.column_header_cell("Description"),
                            rx.table.column_header_cell("Action"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            BetaAIDiagnosisLabState.beta_exercises,
                            exercise_row,
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
            ),
            rx.cond(
                BetaAIDiagnosisLabState.has_selected_exercise,
                rx.callout(
                    "Selected exercise: "
                    + BetaAIDiagnosisLabState.selected_exercise_title,
                    icon="check",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def concept_row(concept: BetaConcept) -> rx.Component:
    """Render one selectable concept row."""
    return rx.table.row(
        rx.table.cell(concept.label),
        rx.table.cell(concept.description, max_width="30em"),
        rx.table.cell(
            rx.button(
                "Select",
                size="2",
                on_click=BetaAIDiagnosisLabState.select_concept(concept.id),
                _hover={"cursor": "pointer"},
            )
        ),
    )


def concept_selection_card() -> rx.Component:
    """Render concept selection for the selected exercise."""
    return rx.card(
        rx.vstack(
            rx.heading("2. Select Concept", size="4"),
            rx.cond(
                ~BetaAIDiagnosisLabState.has_selected_exercise,
                rx.callout("Select an exercise first.", icon="info", width="100%"),
                rx.cond(
                    BetaAIDiagnosisLabState.concepts.length() == 0,  # type: ignore
                    rx.callout(
                        "The selected exercise has no concepts.",
                        icon="triangle-alert",
                        color_scheme="orange",
                        width="100%",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Concept"),
                                rx.table.column_header_cell("Description"),
                                rx.table.column_header_cell("Action"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(BetaAIDiagnosisLabState.concepts, concept_row)
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
            ),
            rx.cond(
                BetaAIDiagnosisLabState.has_selected_concept,
                rx.callout(
                    "Selected concept: "
                    + BetaAIDiagnosisLabState.selected_concept_label,
                    icon="check",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def core_point_item(core_point: BetaCorePoint) -> rx.Component:
    """Render one core point."""
    return rx.list.item(
        rx.hstack(
            rx.badge(core_point.id),
            rx.text(core_point.text),
            align="center",
        )
    )


def misconception_item(misconception: BetaMisconception) -> rx.Component:
    """Render one misconception."""
    return rx.list.item(
        rx.hstack(
            rx.badge(misconception.id),
            rx.text(misconception.label),
            align="center",
        )
    )


def concept_details_card() -> rx.Component:
    """Render selected concept details."""
    return rx.card(
        rx.vstack(
            rx.heading("3. Inspect Concept Data", size="4"),
            rx.cond(
                ~BetaAIDiagnosisLabState.has_selected_concept,
                rx.callout("Select a concept first.", icon="info", width="100%"),
                rx.vstack(
                    rx.text("Core Points", weight="bold"),
                    rx.cond(
                        BetaAIDiagnosisLabState.core_points.length() == 0,  # type: ignore
                        rx.text("No core points saved for this concept."),
                        rx.list.unordered(
                            rx.foreach(
                                BetaAIDiagnosisLabState.core_points,
                                core_point_item,
                            )
                        ),
                    ),
                    rx.text("Misconceptions", weight="bold"),
                    rx.cond(
                        BetaAIDiagnosisLabState.misconceptions.length() == 0,  # type: ignore
                        rx.text("No misconceptions saved for this concept."),
                        rx.list.unordered(
                            rx.foreach(
                                BetaAIDiagnosisLabState.misconceptions,
                                misconception_item,
                            )
                        ),
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def student_answer_card() -> rx.Component:
    """Render the student answer input and diagnosis actions."""
    return rx.card(
        rx.vstack(
            rx.heading("4. Example Student Answer", size="4"),
            rx.text(
                "Run the cheap mock diagnosis for UI checks or call OpenAI for a "
                "structured diagnosis against the selected core points.",
                color_scheme="gray",
                size="2",
            ),
            rx.text_area(
                placeholder="Type a sample student answer here...",
                value=BetaAIDiagnosisLabState.student_answer,
                on_change=BetaAIDiagnosisLabState.set_student_answer,
                rows="5",
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    "Run Mock Diagnosis",
                    on_click=BetaAIDiagnosisLabState.run_mock_diagnosis,
                    disabled=~BetaAIDiagnosisLabState.has_selected_concept,
                    _hover=rx.cond(
                        BetaAIDiagnosisLabState.has_selected_concept,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                ),
                rx.button(
                    "Run LLM Diagnosis",
                    on_click=BetaAIDiagnosisLabState.run_llm_diagnosis,
                    loading=BetaAIDiagnosisLabState.running_llm_diagnosis,
                    disabled=~BetaAIDiagnosisLabState.can_run_diagnosis,
                    color_scheme="blue",
                    _hover=rx.cond(
                        BetaAIDiagnosisLabState.can_run_diagnosis,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                ),
                spacing="3",
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def diagnosis_output_card() -> rx.Component:
    """Render diagnosis output."""
    return rx.card(
        rx.vstack(
            rx.heading("5. Diagnosis Output", size="4"),
            rx.cond(
                BetaAIDiagnosisLabState.has_diagnosis,
                rx.vstack(
                    rx.text(
                        "Final app-normalized pattern",
                        weight="bold",
                    ),
                    rx.hstack(
                        rx.badge(BetaAIDiagnosisLabState.diagnosis_pattern),
                        spacing="2",
                    ),
                    rx.text(
                        "LLM suggested pattern: "
                        + BetaAIDiagnosisLabState.llm_suggested_pattern,
                        size="2",
                        color_scheme="gray",
                    ),
                    rx.cond(
                        BetaAIDiagnosisLabState.has_validation_messages,
                        rx.vstack(
                            rx.cond(
                                BetaAIDiagnosisLabState.diagnosis_validation_errors_text,
                                rx.callout(
                                    BetaAIDiagnosisLabState.diagnosis_validation_errors_text,
                                    icon="triangle-alert",
                                    color_scheme="red",
                                    width="100%",
                                    white_space="pre-wrap",
                                ),
                            ),
                            rx.cond(
                                BetaAIDiagnosisLabState.diagnosis_validation_warnings_text,
                                rx.callout(
                                    BetaAIDiagnosisLabState.diagnosis_validation_warnings_text,
                                    icon="info",
                                    color_scheme="orange",
                                    width="100%",
                                    white_space="pre-wrap",
                                ),
                            ),
                            width="100%",
                            spacing="2",
                        ),
                    ),
                    rx.text(
                        "Task relevance: "
                        + BetaAIDiagnosisLabState.diagnosis_task_relevance
                    ),
                    rx.text(
                        "Correctness: " + BetaAIDiagnosisLabState.diagnosis_correctness
                    ),
                    rx.text(
                        "Completeness: "
                        + BetaAIDiagnosisLabState.diagnosis_completeness
                    ),
                    rx.text("Covered Core Point IDs", weight="bold"),
                    rx.text(BetaAIDiagnosisLabState.diagnosis_covered_core_point_ids),
                    rx.text("Missing Core Point IDs", weight="bold"),
                    rx.text(BetaAIDiagnosisLabState.diagnosis_missing_core_point_ids),
                    rx.text("Evidence Snippets", weight="bold"),
                    rx.text(BetaAIDiagnosisLabState.diagnosis_evidence_snippets),
                    rx.callout(
                        BetaAIDiagnosisLabState.diagnosis_explanation,
                        icon="info",
                        width="100%",
                    ),
                    rx.cond(
                        BetaAIDiagnosisLabState.has_policy_preview,
                        rx.box(
                            rx.vstack(
                                rx.heading("Policy Preview", size="3"),
                                rx.hstack(
                                    rx.text("Rule:", weight="bold"),
                                    rx.badge(
                                        BetaAIDiagnosisLabState.policy_preview_rule_id,
                                        color_scheme="gray",
                                    ),
                                    rx.text("Action:", weight="bold"),
                                    rx.badge(
                                        BetaAIDiagnosisLabState.policy_preview_action,
                                        color_scheme="purple",
                                    ),
                                    align="center",
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                rx.cond(
                                    BetaAIDiagnosisLabState.policy_preview_focus_core_point,
                                    rx.vstack(
                                        rx.text("Focus core point", weight="bold"),
                                        rx.callout(
                                            BetaAIDiagnosisLabState.policy_preview_focus_core_point,
                                            icon="target",
                                            width="100%",
                                        ),
                                        spacing="1",
                                        width="100%",
                                        align="start",
                                    ),
                                ),
                                rx.text("Feedback brief", weight="bold"),
                                rx.text(
                                    BetaAIDiagnosisLabState.policy_preview_feedback_brief
                                ),
                                rx.text("Rationale", weight="bold"),
                                rx.text(
                                    BetaAIDiagnosisLabState.policy_preview_rationale
                                ),
                                rx.text("Suggested tutor prompt", weight="bold"),
                                rx.callout(
                                    BetaAIDiagnosisLabState.policy_preview_suggested_prompt,
                                    icon="message-circle-question",
                                    width="100%",
                                ),
                                align="start",
                                spacing="2",
                                width="100%",
                            ),
                            padding="1em",
                            background_color=rx.color("purple", 2),
                            border_radius="8px",
                            width="100%",
                        ),
                    ),
                    rx.cond(
                        BetaAIDiagnosisLabState.has_diagnosis_trace,
                        rx.box(
                            rx.vstack(
                                rx.heading("Audit Trace Preview", size="3"),
                                rx.text(
                                    "Replayable preview of the diagnosis, "
                                    "validation, and selected policy rule. "
                                    "Not persisted yet.",
                                    size="2",
                                    color_scheme="gray",
                                ),
                                rx.code_block(
                                    BetaAIDiagnosisLabState.diagnosis_trace_json,
                                    language="json",
                                    width="100%",
                                ),
                                align="start",
                                spacing="2",
                                width="100%",
                            ),
                            padding="1em",
                            background_color=rx.color("gray", 2),
                            border_radius="8px",
                            width="100%",
                        ),
                    ),
                    align="start",
                    spacing="2",
                    width="100%",
                ),
                rx.callout(
                    "No diagnosis yet. Select a concept, enter an answer, "
                    "and run a diagnosis.",
                    icon="info",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def beta_ai_diagnosis_lab_content() -> rx.Component:
    """Render the full Diagnosis Lab skeleton."""
    return rx.vstack(
        diagnosis_lab_header(),
        exercise_selection_card(),
        concept_selection_card(),
        concept_details_card(),
        student_answer_card(),
        diagnosis_output_card(),
        spacing="4",
        width="100%",
    )
