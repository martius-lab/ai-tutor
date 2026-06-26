"""Components for the Beta AI exercise builder page."""

import reflex as rx

from aitutor.beta_ai.schemas import SavedConceptDetail
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
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Inspect",
                    size="2",
                    on_click=BetaAIExercisesState.select_saved_exercise(exercise.id),
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    "Delete",
                    size="2",
                    variant="soft",
                    color_scheme="red",
                    on_click=BetaAIExercisesState.delete_saved_exercise(exercise.id),
                    _hover={"cursor": "pointer"},
                ),
                spacing="2",
            )
        ),
    )


def saved_concept_detail_card(concept: SavedConceptDetail) -> rx.Component:
    """Render one persisted concept with its saved core points and misconceptions."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(concept.concept_id),
                rx.heading(concept.label, size="3"),
                align="center",
                spacing="2",
                wrap="wrap",
            ),
            rx.cond(
                concept.description,
                rx.text(concept.description, color_scheme="gray"),
            ),
            rx.text("Core Points", weight="bold"),
            rx.cond(
                concept.core_points.length() == 0,  # type: ignore
                rx.text("No core points saved for this concept.", size="2"),
                rx.list.unordered(rx.foreach(concept.core_points, rx.list.item)),
            ),
            rx.text("Misconceptions", weight="bold"),
            rx.cond(
                concept.misconceptions.length() == 0,  # type: ignore
                rx.text("No misconceptions saved for this concept.", size="2"),
                rx.list.unordered(rx.foreach(concept.misconceptions, rx.list.item)),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def saved_exercise_detail_card() -> rx.Component:
    """Render the selected saved exercise's persisted concept registry."""
    return rx.cond(
        BetaAIExercisesState.has_selected_saved_exercise,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Saved Exercise Details", size="4"),
                    rx.spacer(),
                    rx.button(
                        "Close",
                        size="2",
                        variant="outline",
                        on_click=BetaAIExercisesState.clear_selected_saved_exercise,
                        _hover={"cursor": "pointer"},
                    ),
                    width="100%",
                ),
                rx.text(
                    "Title: " + BetaAIExercisesState.selected_saved_exercise_title,
                    weight="bold",
                ),
                rx.cond(
                    BetaAIExercisesState.selected_saved_exercise_description,
                    rx.text(
                        "Description: "
                        + BetaAIExercisesState.selected_saved_exercise_description
                    ),
                ),
                rx.cond(
                    BetaAIExercisesState.selected_saved_exercise_source_file,
                    rx.callout(
                        "Source file: "
                        + BetaAIExercisesState.selected_saved_exercise_source_file,
                        icon="file-text",
                        width="100%",
                    ),
                ),
                rx.text("Persisted Concept Registry", weight="bold"),
                rx.cond(
                    BetaAIExercisesState.selected_saved_concepts.length() == 0,  # type: ignore
                    rx.callout(
                        "No concepts saved for this exercise.",
                        icon="info",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.foreach(
                            BetaAIExercisesState.selected_saved_concepts,
                            saved_concept_detail_card,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            width="100%",
        ),
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
                            rx.table.column_header_cell("Actions"),
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
            saved_exercise_detail_card(),
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
                placeholder="Description (optional)",
                value=BetaAIExercisesState.description,
                on_change=BetaAIExercisesState.set_description,
                rows="4",
                width="100%",
            ),
            rx.vstack(
                rx.text("Generation targets", weight="bold", size="2"),
                rx.text(
                    "Approximate counts used by the AI prompt.",
                    size="2",
                    color_scheme="gray",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Concepts", size="2"),
                        rx.input(
                            value=BetaAIExercisesState.concept_target_count_str,
                            on_change=BetaAIExercisesState.set_concept_target_count,
                            type="number",
                            min="1",
                            max="30",
                            width="100%",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Core points", size="2"),
                        rx.input(
                            value=BetaAIExercisesState.core_point_target_count_str,
                            on_change=BetaAIExercisesState.set_core_point_target_count,
                            type="number",
                            min="1",
                            max="15",
                            width="100%",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Misconceptions", size="2"),
                        rx.input(
                            value=BetaAIExercisesState.misconception_target_count_str,
                            on_change=BetaAIExercisesState.set_misconception_target_count,
                            type="number",
                            min="1",
                            max="10",
                            width="100%",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    wrap="wrap",
                ),
                align="start",
                spacing="2",
                width="100%",
                padding="1em",
                background_color=rx.color("gray", 2),
                border_radius="8px",
            ),
            rx.button(
                rx.icon("sparkles"),
                BetaAIExercisesState.generate_concepts_button_label,
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
    """Render one editable concept as a compact expandable item."""
    return rx.el.details(
        rx.el.summary(
            rx.hstack(
                rx.hstack(
                    rx.icon("chevron-right", size=16, color="gray"),
                    rx.badge("Concept", variant="soft"),
                    rx.text(concept.label, weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("trash", size=16),
                    color_scheme="red",
                    variant="ghost",
                    size="2",
                    on_click=BetaAIExercisesState.delete_concept(concept_index),
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
                align="center",
            ),
            padding="0.85em 1em",
            border_radius="8px",
            _hover={
                "cursor": "pointer",
                "background_color": rx.color("gray", 3),
            },
            list_style="none",
        ),
        rx.vstack(
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
            rx.vstack(
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
                align="start",
                spacing="2",
                width="100%",
            ),
            rx.vstack(
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
                align="start",
                spacing="2",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
            padding="1em",
            padding_top="0.5em",
        ),
        border="1px solid var(--gray-6)",
        border_radius="10px",
        background_color=rx.color("gray", 1),
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
            rx.vstack(
                rx.foreach(BetaAIExercisesState.generated_concepts, concept_card),
                spacing="3",
                width="100%",
            ),
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
        width="42em",
        max_width="90vw",
    )
