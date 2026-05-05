"""Components for the Beta AI exercise builder page."""

import reflex as rx

from aitutor.models import BetaExercise
from aitutor.pages.beta_ai_exercises.state import BetaAIExercisesState


def builder_header() -> rx.Component:
    """Render the page header."""
    return rx.vstack(
        rx.heading("Beta AI", size="7"),
        rx.text(
            "Create independent Beta AI Tutor exercises from PDFs",
            color_scheme="gray",
        ),
        align="start",
        spacing="1",
        width="100%",
    )


def saved_exercise_row(exercise: BetaExercise) -> rx.Component:
    """Render one saved Beta AI exercise row."""
    return rx.table.row(
        rx.table.cell(exercise.title),
        rx.table.cell(exercise.description, max_width="30em"),
        rx.table.cell(exercise.source_material_filename),
    )


def saved_exercises_table() -> rx.Component:
    """Render saved Beta AI exercises."""
    return rx.card(
        rx.vstack(
            rx.heading("Saved Beta AI Exercises", size="4"),
            rx.cond(
                BetaAIExercisesState.beta_exercises.length() == 0,  # type: ignore
                rx.callout(
                    "No Beta AI exercises saved yet.", icon="info", width="100%"
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Title"),
                            rx.table.column_header_cell("Description"),
                            rx.table.column_header_cell("Source file"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            BetaAIExercisesState.beta_exercises,
                            saved_exercise_row,
                        )
                    ),
                    variant="surface",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def source_material_card() -> rx.Component:
    """Render PDF upload and source preview."""
    return rx.card(
        rx.vstack(
            rx.heading("1. Source material", size="4"),
            rx.upload(
                rx.vstack(
                    rx.button(
                        "Select PDF",
                        type="button",
                        loading=BetaAIExercisesState.extracting_source_material,
                        disabled=BetaAIExercisesState.extracting_source_material,
                    ),
                    rx.text("Drop one or more lecture PDFs here."),
                    rx.text(rx.selected_files("beta_ai_pdf_upload"), color="yellow"),
                    align="center",
                ),
                id="beta_ai_pdf_upload",
                accept={"application/pdf": [".pdf"]},
                padding="2em",
                border="1px dashed var(--gray-8)",
                border_radius="8px",
                on_drop=BetaAIExercisesState.extract_source_material(
                    rx.upload_files(upload_id="beta_ai_pdf_upload")  # type: ignore
                ),
                _hover={"cursor": "pointer"},
                width="100%",
            ),
            rx.cond(
                BetaAIExercisesState.source_material_filename,
                rx.callout(
                    BetaAIExercisesState.source_material_filename,
                    icon="file-text",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            rx.cond(
                BetaAIExercisesState.source_material_preview,
                rx.box(
                    rx.text("Preview", weight="bold", size="2"),
                    rx.text(
                        BetaAIExercisesState.source_material_preview,
                        size="2",
                        color_scheme="gray",
                    ),
                    padding="1em",
                    background_color=rx.color("gray", 2),
                    border_radius="8px",
                    width="100%",
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def metadata_card() -> rx.Component:
    """Render title, description, and generate button."""
    return rx.card(
        rx.vstack(
            rx.heading("2. Exercise metadata", size="4"),
            rx.input(
                placeholder="Title",
                value=BetaAIExercisesState.title,
                on_change=BetaAIExercisesState.set_title,
                width="100%",
            ),
            rx.text_area(
                placeholder="Description",
                value=BetaAIExercisesState.description,
                on_change=BetaAIExercisesState.set_description,
                rows="4",
                width="100%",
            ),
            rx.button(
                rx.icon("sparkles"),
                "Generate Concepts",
                on_click=BetaAIExercisesState.generate_concepts,
                loading=BetaAIExercisesState.generating_concepts,
                disabled=~BetaAIExercisesState.can_generate_concepts,
                _hover=rx.cond(
                    BetaAIExercisesState.can_generate_concepts,
                    {"cursor": "pointer"},
                    {"cursor": "not-allowed"},
                ),
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def core_point_row(concept_index, core_point, core_point_index) -> rx.Component:
    """Render one editable core point."""
    return rx.hstack(
        rx.text_area(
            value=core_point.text,
            on_change=lambda value: BetaAIExercisesState.set_core_point_text(
                concept_index, core_point_index, value
            ),
            rows="2",
            width="100%",
        ),
        rx.switch(
            checked=core_point.required,
            on_change=lambda value: BetaAIExercisesState.set_core_point_required(
                concept_index, core_point_index, value
            ),
        ),
        rx.icon_button(
            rx.icon("trash", size=16),
            variant="ghost",
            color_scheme="red",
            on_click=BetaAIExercisesState.delete_core_point(
                concept_index, core_point_index
            ),
            _hover={"cursor": "pointer"},
        ),
        align="center",
        width="100%",
    )


def misconception_row(
    concept_index, misconception, misconception_index
) -> rx.Component:
    """Render one editable misconception."""
    return rx.hstack(
        rx.input(
            value=misconception.label,
            on_change=lambda value: BetaAIExercisesState.set_misconception_label(
                concept_index, misconception_index, value
            ),
            width="100%",
        ),
        rx.icon_button(
            rx.icon("trash", size=16),
            variant="ghost",
            color_scheme="red",
            on_click=BetaAIExercisesState.delete_misconception(
                concept_index, misconception_index
            ),
            _hover={"cursor": "pointer"},
        ),
        width="100%",
    )


def concept_card(concept, concept_index) -> rx.Component:
    """Render one editable concept card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge("Concept"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("trash"),
                    color_scheme="red",
                    variant="ghost",
                    on_click=BetaAIExercisesState.delete_concept(concept_index),
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
            ),
            rx.input(
                value=concept.label,
                on_change=lambda value: BetaAIExercisesState.set_concept_label(
                    concept_index, value
                ),
                placeholder="Concept label",
                width="100%",
            ),
            rx.text_area(
                value=concept.description,
                on_change=lambda value: BetaAIExercisesState.set_concept_description(
                    concept_index, value
                ),
                placeholder="Concept description",
                rows="3",
                width="100%",
            ),
            rx.text("Core Points", weight="bold"),
            rx.foreach(
                concept.core_points,
                lambda core_point, core_point_index: core_point_row(
                    concept_index, core_point, core_point_index
                ),
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Add Core Point",
                size="2",
                variant="soft",
                on_click=BetaAIExercisesState.add_core_point(concept_index),
                _hover={"cursor": "pointer"},
            ),
            rx.text("Misconceptions", weight="bold"),
            rx.foreach(
                concept.misconceptions,
                lambda misconception, misconception_index: misconception_row(
                    concept_index, misconception, misconception_index
                ),
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Add Misconception",
                size="2",
                variant="soft",
                on_click=BetaAIExercisesState.add_misconception(concept_index),
                _hover={"cursor": "pointer"},
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def concepts_card() -> rx.Component:
    """Render generated concept editor."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("3. Review concepts", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus"),
                    "Add Concept",
                    variant="soft",
                    on_click=BetaAIExercisesState.add_concept,
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
            ),
            rx.cond(
                BetaAIExercisesState.generated_concepts.length() == 0,  # type: ignore
                rx.callout(
                    "No concepts yet. Upload a PDF and generate concepts.",
                    icon="info",
                    width="100%",
                ),
            ),
            rx.foreach(BetaAIExercisesState.generated_concepts, concept_card),
            rx.hstack(
                rx.button(
                    "Reset",
                    variant="outline",
                    on_click=BetaAIExercisesState.reset_builder,
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    rx.icon("save"),
                    "Save Beta AI Exercise",
                    color_scheme="green",
                    on_click=BetaAIExercisesState.save_beta_exercise,
                    loading=BetaAIExercisesState.saving_exercise,
                    disabled=~BetaAIExercisesState.can_save_exercise,
                ),
                justify="end",
                width="100%",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def beta_ai_exercises_content() -> rx.Component:
    """Render the full Beta AI exercises page content."""
    return rx.vstack(
        builder_header(),
        saved_exercises_table(),
        rx.divider(),
        source_material_card(),
        metadata_card(),
        concepts_card(),
        spacing="4",
        width="100%",
    )
