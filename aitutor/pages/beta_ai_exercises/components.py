"""Components for the Better AI builder dialog in lecture exercise management."""

import reflex as rx

from aitutor.global_vars import TIME_ZONE
from aitutor.language_state import LanguageState as LS
from aitutor.pages.beta_ai_exercises.state import BetaAIExercisesState
from aitutor.pages.lecture_manage_exercises.state import (
    LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS,
)


def source_material_card() -> rx.Component:
    """Render PDF upload and source preview."""
    return rx.card(
        rx.vstack(
            rx.heading(LS.beta_ai_source_material, size="4"),
            rx.upload(
                rx.vstack(
                    rx.button(
                        LS.beta_ai_select_pdf,
                        type="button",
                        loading=BetaAIExercisesState.extracting_source_material,
                        disabled=(
                            BetaAIExercisesState.extracting_source_material
                            | BetaAIExercisesState.exercise_has_started
                        ),
                    ),
                    rx.text(LS.beta_ai_drop_pdfs),
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
                disabled=BetaAIExercisesState.exercise_has_started,
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
                    rx.text(LS.beta_ai_preview, weight="bold", size="2"),
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
            rx.heading(LS.beta_ai_exercise_metadata, size="4"),
            rx.cond(
                BetaAIExercisesState.exercise_has_started,
                rx.callout(
                    LS.beta_ai_started_exercise_content_locked,
                    icon="lock",
                    color_scheme="orange",
                    width="100%",
                ),
            ),
            rx.input(
                placeholder=LS.exercise_title_placeholder,
                value=BetaAIExercisesState.title,
                on_change=BetaAIExercisesState.set_title,
                max_length=LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["title"],
                width="100%",
            ),
            rx.text_area(
                placeholder=LS.description_placeholder,
                value=BetaAIExercisesState.description,
                on_change=BetaAIExercisesState.set_description,
                disabled=BetaAIExercisesState.exercise_has_started,
                max_length=LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS["description"],
                rows="4",
                width="100%",
            ),
            rx.vstack(
                rx.text(LS.beta_ai_generation_targets, weight="bold", size="2"),
                rx.text(
                    LS.beta_ai_generation_targets_info,
                    size="2",
                    color_scheme="gray",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(LS.beta_ai_concepts, size="2"),
                        rx.input(
                            value=BetaAIExercisesState.concept_target_count_str,
                            on_change=BetaAIExercisesState.set_concept_target_count,
                            type="number",
                            min="1",
                            max="30",
                            disabled=BetaAIExercisesState.exercise_has_started,
                            width="100%",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(LS.beta_ai_core_points, size="2"),
                        rx.input(
                            value=BetaAIExercisesState.core_point_target_count_str,
                            on_change=BetaAIExercisesState.set_core_point_target_count,
                            type="number",
                            min="1",
                            max="15",
                            disabled=BetaAIExercisesState.exercise_has_started,
                            width="100%",
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(LS.beta_ai_misconceptions, size="2"),
                        rx.input(
                            value=BetaAIExercisesState.misconception_target_count_str,
                            on_change=BetaAIExercisesState.set_misconception_target_count,
                            type="number",
                            min="1",
                            max="10",
                            disabled=BetaAIExercisesState.exercise_has_started,
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
                rx.cond(
                    BetaAIExercisesState.generated_concepts.length() > 0,  # type: ignore
                    LS.beta_ai_regenerate_concepts,
                    LS.beta_ai_generate_concepts,
                ),
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
            disabled=BetaAIExercisesState.exercise_has_started,
            width="100%",
        ),
        rx.icon_button(
            rx.icon("trash", size=16),
            variant="ghost",
            color_scheme="red",
            on_click=BetaAIExercisesState.delete_core_point(
                concept_index, core_point_index
            ),
            disabled=BetaAIExercisesState.exercise_has_started,
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
        rx.text_area(
            value=misconception.label,
            on_change=lambda value: BetaAIExercisesState.set_misconception_label(
                concept_index, misconception_index, value
            ),
            rows="2",
            disabled=BetaAIExercisesState.exercise_has_started,
            width="100%",
        ),
        rx.icon_button(
            rx.icon("trash", size=16),
            variant="ghost",
            color_scheme="red",
            on_click=BetaAIExercisesState.delete_misconception(
                concept_index, misconception_index
            ),
            disabled=BetaAIExercisesState.exercise_has_started,
            _hover={"cursor": "pointer"},
        ),
        align="center",
        width="100%",
    )


def concept_card(concept, concept_index) -> rx.Component:
    """Render one editable concept as a compact expandable item."""
    return rx.el.details(
        rx.el.summary(
            rx.hstack(
                rx.hstack(
                    rx.icon("chevron-right", size=16, color="gray"),
                    rx.badge(LS.beta_ai_concept, variant="soft"),
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
                    disabled=BetaAIExercisesState.exercise_has_started,
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
                placeholder=LS.beta_ai_concepts,
                disabled=BetaAIExercisesState.exercise_has_started,
                width="100%",
            ),
            rx.text_area(
                value=concept.description,
                on_change=lambda value: BetaAIExercisesState.set_concept_description(
                    concept_index, value
                ),
                placeholder=LS.description,
                rows="3",
                disabled=BetaAIExercisesState.exercise_has_started,
                width="100%",
            ),
            rx.vstack(
                rx.text(LS.beta_ai_core_points, weight="bold"),
                rx.foreach(
                    concept.core_points,
                    lambda core_point, core_point_index: core_point_row(
                        concept_index, core_point, core_point_index
                    ),
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    LS.beta_ai_add_core_point,
                    size="2",
                    variant="soft",
                    on_click=BetaAIExercisesState.add_core_point(concept_index),
                    disabled=BetaAIExercisesState.exercise_has_started,
                    _hover={"cursor": "pointer"},
                ),
                align="start",
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text(LS.beta_ai_misconceptions, weight="bold"),
                rx.foreach(
                    concept.misconceptions,
                    lambda misconception, misconception_index: misconception_row(
                        concept_index, misconception, misconception_index
                    ),
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    LS.beta_ai_add_misconception,
                    size="2",
                    variant="soft",
                    on_click=BetaAIExercisesState.add_misconception(concept_index),
                    disabled=BetaAIExercisesState.exercise_has_started,
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


def deadline_fields() -> rx.Component:
    """Render the deadline controls for a Beta AI exercise."""
    return rx.vstack(
        rx.hstack(
            rx.text(LS.activate_deadline, size="3", weight="medium"),
            rx.checkbox(
                checked=BetaAIExercisesState.use_deadline,
                on_change=BetaAIExercisesState.set_use_deadline,
            ),
            align="center",
        ),
        rx.cond(
            BetaAIExercisesState.use_deadline,
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(LS.deadline, size="3", weight="medium"),
                        rx.input(
                            value=BetaAIExercisesState.deadline,
                            on_change=BetaAIExercisesState.set_deadline,
                            type="datetime-local",
                        ),
                        align="start",
                    ),
                    rx.vstack(
                        rx.text(
                            LS.days_to_complete,
                            size="3",
                            weight="medium",
                        ),
                        rx.input(
                            placeholder="e.g. 7",
                            value=BetaAIExercisesState.days_to_complete,
                            on_change=BetaAIExercisesState.set_days_to_complete,
                            type="number",
                            step="1",
                            min="1",
                            max_length=LECTURE_MANAGE_EXERCISES_FIELD_MAX_LENGTHS[
                                "days_to_complete"
                            ],
                        ),
                        align="start",
                    ),
                    spacing="3",
                    wrap="wrap",
                ),
                rx.text(LS.timezone + TIME_ZONE),
                align="start",
            ),
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def concepts_card() -> rx.Component:
    """Render generated concept editor."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(LS.beta_ai_review_concepts, size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus"),
                    LS.beta_ai_add_concept,
                    variant="soft",
                    on_click=BetaAIExercisesState.add_concept,
                    disabled=BetaAIExercisesState.exercise_has_started,
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
            ),
            rx.cond(
                BetaAIExercisesState.generated_concepts.length() == 0,  # type: ignore
                rx.callout(
                    LS.beta_ai_no_concepts_yet,
                    icon="info",
                    width="100%",
                ),
            ),
            rx.vstack(
                rx.foreach(BetaAIExercisesState.generated_concepts, concept_card),
                spacing="3",
                width="100%",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def new_tag_dialog() -> rx.Component:
    """Render the add-tag interaction for the Better AI builder."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.hstack(
                    rx.icon("plus", size=18),
                    rx.icon("tag", size=18),
                    align="center",
                    spacing="1",
                ),
                LS.new_tag,
                type="button",
                _hover={"cursor": "pointer"},
            )
        ),
        rx.dialog.content(
            rx.vstack(
                rx.heading(LS.new_tag),
                rx.input(
                    placeholder=LS.tagname,
                    value=BetaAIExercisesState.new_tag_name,
                    on_change=BetaAIExercisesState.set_new_tag_name,
                    on_key_down=lambda key: rx.cond(
                        key == "Enter", BetaAIExercisesState.add_new_tag, None
                    ),
                    max_length=100,
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(LS.cancel, variant="outline", type="button")
                    ),
                    rx.button(
                        LS.add_tag,
                        on_click=BetaAIExercisesState.add_new_tag,
                        disabled=BetaAIExercisesState.new_tag_name == "",
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
            width="20em",
            max_width="90vw",
        ),
        open=BetaAIExercisesState.add_tag_dialog_is_open,
        on_open_change=BetaAIExercisesState.set_add_tag_dialog_is_open,
    )


def tag_selection() -> rx.Component:
    """Render lecture tag selection using the regular exercise interaction."""
    return rx.vstack(
        rx.text(LS.tags + ":", size="3", weight="medium"),
        rx.hstack(
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("list", size=18),
                        LS.select_tags,
                        type="button",
                        _hover={"cursor": "pointer"},
                    )
                ),
                rx.menu.content(
                    rx.foreach(
                        BetaAIExercisesState.selectable_tags,
                        lambda tag_name: rx.menu.item(
                            tag_name,
                            on_click=BetaAIExercisesState.add_to_selected_tags(
                                tag_name
                            ),
                        ),
                    ),
                    min_width="10em",
                ),
            ),
            new_tag_dialog(),
            align="center",
            justify="between",
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                BetaAIExercisesState.selected_tags,
                lambda tag: rx.badge(
                    rx.hstack(
                        rx.text(tag),
                        rx.icon("circle-x", size=16),
                        spacing="1",
                        align_items="center",
                    ),
                    on_click=BetaAIExercisesState.remove_selected_tag(tag),
                    cursor="pointer",
                    size="3",
                ),
            ),
            spacing="1",
            wrap="wrap",
        ),
        align="start",
        spacing="2",
        width="100%",
    )


def exercise_settings_card() -> rx.Component:
    """Render visibility, deadline, and save controls."""
    return rx.card(
        rx.vstack(
            rx.heading(LS.beta_ai_exercise_settings, size="4"),
            rx.hstack(
                rx.text(LS.hide_exercise, size="3", weight="medium"),
                rx.checkbox(
                    checked=BetaAIExercisesState.is_hidden,
                    on_change=BetaAIExercisesState.set_is_hidden,
                ),
                align="center",
            ),
            deadline_fields(),
            tag_selection(),
            rx.hstack(
                rx.button(
                    rx.cond(
                        BetaAIExercisesState.builder_dialog_is_open,
                        LS.cancel,
                        rx.cond(
                            BetaAIExercisesState.is_editing,
                            LS.cancel,
                            LS.reset_string,
                        ),
                    ),
                    variant="outline",
                    on_click=rx.cond(
                        BetaAIExercisesState.builder_dialog_is_open,
                        BetaAIExercisesState.close_builder_dialog,
                        rx.cond(
                            BetaAIExercisesState.is_editing,
                            BetaAIExercisesState.cancel_builder,
                            BetaAIExercisesState.reset_builder,
                        ),
                    ),
                    _hover={"cursor": "pointer"},
                ),
                rx.button(
                    rx.icon("save"),
                    rx.cond(
                        BetaAIExercisesState.is_editing,
                        LS.update_task,
                        LS.beta_ai_save_exercise,
                    ),
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


def beta_ai_exercise_builder() -> rx.Component:
    """Render the form for creating or editing a Beta AI exercise."""
    return rx.vstack(
        source_material_card(),
        metadata_card(),
        concepts_card(),
        exercise_settings_card(),
        spacing="4",
        width="100%",
    )
