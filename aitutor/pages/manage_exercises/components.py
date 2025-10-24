"""The Components for the manage exercises page."""

from typing import Sequence

import reflex as rx

from aitutor.models import Exercise
from aitutor.pages.manage_exercises.state import ManageExercisesState, DialogMode
from aitutor.utilities.helper_functions import truncate_text_reflex_var
from aitutor.global_vars import TIME_ZONE
from aitutor.language_state import LanguageState


def new_tag_dialog():
    """Dialog for adding new tags."""
    return (
        rx.dialog.root(
            rx.dialog.trigger(
                rx.button(
                    LanguageState.new_tag,
                    margin_top="0.5em",
                    color_scheme="orange",
                    shade="7",
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.dialog.content(
                rx.form(
                    rx.input(
                        placeholder=LanguageState.tagname,
                        name="tag",
                    ),
                    rx.center(
                        rx.dialog.close(
                            rx.button(
                                rx.text(LanguageState.cancel),
                                color_scheme="red",
                                type="button",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        rx.form.submit(
                            rx.button(
                                LanguageState.add_tag,
                                color_scheme="grass",
                                type="submit",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        padding_top="1em",
                        spacing="2",
                    ),
                    # submit new tags
                    on_submit=ManageExercisesState.submit_tag,
                ),
            ),
            open=ManageExercisesState.add_tag_dialog_is_open,
            on_open_change=ManageExercisesState.set_add_tag_dialog_is_open,
        ),
    )


def delete_exercise_button(exercise: Exercise):
    """Delete exercise"""
    return (
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.icon_button(
                    rx.icon("trash"),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title(LanguageState.delete_exercise),
                rx.alert_dialog.description(LanguageState.delete_exercise_info),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            rx.text(LanguageState.cancel),
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            LanguageState.confirm,
                            color_scheme="iris",
                            on_click=ManageExercisesState.delete_exercise(exercise.id),  # type: ignore
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    margin_top="1em",
                ),
            ),
        ),
    )


def show_exercise(exercise: Exercise):
    """Show exercises on page in a table row."""
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(
                checked=ManageExercisesState.exercise_is_checked[exercise.id],  # type: ignore
                on_change=lambda checked: ManageExercisesState.set_exercise_is_checked(
                    exercise.id, checked
                ),
            )
        ),
        rx.table.cell(exercise.title, max_width="175px"),
        rx.table.cell(
            truncate_text_reflex_var(exercise.description, max_length=150),
            max_width="400px",
        ),
        rx.table.cell(
            rx.hstack(
                rx.foreach(
                    exercise.tags,
                    lambda tag: rx.badge(
                        tag.name,
                        variant="soft",
                        color_scheme="blue",
                        on_click=ManageExercisesState.add_search_value(
                            {"search_value": f'tag:"{tag.name}"'}
                        ),
                        _hover={"cursor": "pointer"},
                    ),
                ),
                spacing="1",
                wrap="wrap",
            )
        ),
        rx.table.cell(
            ManageExercisesState.editing_periods[exercise.id]  # type: ignore
        ),
        rx.table.cell(
            rx.hstack(
                hide_exercise_button(exercise),
                edit_exercise_button(exercise),
                delete_exercise_button(exercise),
                spacing="5",
            ),
        ),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def header_cell(text, icon: str):
    """Create header cells."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="3",
        ),
    )


def exercise_table():
    """The main table"""
    return (
        rx.fragment(
            # head cells for the main table
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(
                            rx.checkbox(
                                checked=ManageExercisesState.all_exercises_checked,
                                on_change=ManageExercisesState.set_all_exercises_checked,
                            ),
                        ),
                        header_cell(LanguageState.exercise, "book"),
                        header_cell(LanguageState.description, "book-open-text"),
                        header_cell(LanguageState.tags, "tag"),
                        header_cell(LanguageState.editing_period, "calendar-clock"),
                        header_cell(LanguageState.settings, "cog"),
                    ),
                ),
                # dynamically render each new entry
                rx.table.body(
                    rx.foreach(ManageExercisesState.exercises, show_exercise)
                ),
                variant="surface",
                size="3",
                width="85vw",
                overflow_y="auto",
                max_height="66vh",
            ),
            edit_exercise_dialog(),
            add_exercise_dialog(),
        ),
    )


def hide_exercise_button(exercise: Exercise):
    """Button to hide or unhide exercise."""
    return (
        rx.center(
            rx.cond(
                exercise.is_hidden,
                rx.icon("eye-off", size=18),
                rx.cond(
                    ManageExercisesState.exercise_is_started[exercise.id],  # type: ignore
                    rx.icon("eye", size=18),
                    rx.hover_card.root(
                        rx.hover_card.trigger(
                            rx.icon("view", size=18),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.hover_card.content(
                            rx.text(
                                LanguageState.exercise_hidden_hover_info,
                            ),
                        ),
                    ),
                ),
            ),
            _hover={"cursor": "pointer"},
            on_click=ManageExercisesState.toggle_visibility(exercise),
        ),
    )


def add_exercise_button() -> rx.Component:
    """Button for adding new exercises."""
    return rx.button(
        rx.icon("file-plus", size=26),
        rx.text(LanguageState.add_exercise, size="4"),
        size="3",
        _hover={"cursor": "pointer"},
        on_click=ManageExercisesState.open_add_dialog,
        type="button",
    )


def add_exercise_dialog() -> rx.Component:
    """Dialog for adding new exercises."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="file-plus", size=34),
                    color_scheme="grass",
                    radius="full",
                ),
                rx.vstack(
                    rx.dialog.title(
                        LanguageState.add_exercise,
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        LanguageState.add_exercise_description,
                    ),
                    spacing="1",
                    height="100%",
                    align_items="start",
                    justify_content="start",
                ),
                height="100%",
                spacing="4",
                margin_bottom="1.5em",
                align_items="start",
                width="100%",
            ),
            rx.form(
                add_edit_exercise_form(mode=DialogMode.ADD),
                on_mount=ManageExercisesState.load_tags,
                on_submit=ManageExercisesState.add_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            new_tag_dialog(),
            on_escape_key_down=ManageExercisesState.close_dialog,
        ),
        open=ManageExercisesState.add_exercise_dialog_is_open,
    )


def edit_exercise_button(exercise: Exercise):
    """Button to open the edit exercise dialog."""
    return rx.button(
        rx.icon("wrench", size=22),
        color_scheme="orange",
        size="2",
        variant="ghost",
        on_click=ManageExercisesState.open_edit_dialog(exercise),
        _hover={"cursor": "pointer"},
        type="button",
    )


def edit_exercise_dialog() -> rx.Component:
    """Dialog for editing exercises."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="wrench", size=34),
                    color_scheme="orange",
                    radius="full",
                ),
                rx.vstack(
                    rx.dialog.title(
                        LanguageState.edit_exercise,
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        LanguageState.edit_exercise_description,
                    ),
                    spacing="1",
                    height="100%",
                    align_items="start",
                    justify_content="start",
                ),
                height="100%",
                spacing="4",
                margin_bottom="1.5em",
                align_items="start",
                width="100%",
            ),
            rx.form(
                add_edit_exercise_form(mode=DialogMode.EDIT),
                on_mount=ManageExercisesState.load_tags,
                on_submit=ManageExercisesState.update_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            new_tag_dialog(),
            on_escape_key_down=ManageExercisesState.close_dialog,
        ),
        open=ManageExercisesState.edit_exercise_dialog_is_open,
    )


def pdf_upload() -> rx.Component:
    """Upload area for lesson material in PDF format."""
    return (
        rx.text(
            LanguageState.add_lesson_context_pdf,
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.upload(
            rx.vstack(
                rx.button(
                    LanguageState.select_file,
                    type="button",
                    _hover=rx.cond(
                        ManageExercisesState.extracting_lesson_material,
                        {"cursor": "not-allowed"},
                        {"cursor": "pointer"},
                    ),
                    loading=ManageExercisesState.extracting_lesson_material,
                    disabled=ManageExercisesState.extracting_lesson_material,
                ),
                rx.text(
                    LanguageState.pdf_upload_info,
                ),
                rx.text(rx.selected_files("upload1"), color="yellow", size="3"),
                align="center",
            ),
            id="upload1",
            padding="5em",
            padding_top="1em",
            padding_bottom="1em",
            on_drop=ManageExercisesState.extract_lesson_material(
                rx.upload_files(upload_id="upload1")  # type: ignore
            ),
        ),
        rx.text(
            LanguageState.last_uploaded_file,
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        # show file icon with file name
        rx.cond(
            ManageExercisesState.lesson_file_name,
            rx.box(
                rx.hstack(
                    rx.icon("file-text", size=25),
                    rx.text(ManageExercisesState.lesson_file_name, color="green"),
                ),
            ),
        ),
    )


def select_prompt(mode: DialogMode) -> rx.Component:
    """The prompt selection component."""
    return (
        rx.text(
            LanguageState.prompt,
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.hstack(
            rx.select(
                items=ManageExercisesState.prompt_names,
                placeholder=LanguageState.select_prompt,
                value=ManageExercisesState.current_prompt_name,
                on_change=ManageExercisesState.set_current_prompt_name,
                multiple=True,
            ),
            # hover to show the prompt
            rx.popover.root(
                rx.popover.trigger(
                    rx.icon("info", size=20),
                    _hover={"cursor": "pointer"},
                ),
                rx.popover.content(
                    rx.flex(
                        rx.cond(
                            mode == DialogMode.ADD,
                            rx.text(
                                ManageExercisesState.prompts[
                                    ManageExercisesState.current_prompt_name
                                ],
                                padding="1em",
                            ),
                            rx.text(
                                # show the prompt from the db or
                                # the selected prompt template
                                rx.cond(
                                    ManageExercisesState.current_exercise.prompt_name
                                    == ManageExercisesState.current_prompt_name,
                                    ManageExercisesState.current_exercise.prompt,
                                    ManageExercisesState.prompts[
                                        ManageExercisesState.current_prompt_name
                                    ],
                                ),
                                padding="1em",
                            ),
                        ),
                        style={
                            "white-space": "pre-wrap",
                            "word-break": "break-word",
                            "overflow_y": "auto",
                            "max_height": "40vh",
                        },
                    )
                ),
            ),
            # center horizontally
            align_items="center",
        ),
    )  # type: ignore


def tag_management() -> rx.Component:
    """Tag selection component"""
    return (
        rx.text(
            LanguageState.tags + ":",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.hstack(
            rx.hstack(
                rx.center(
                    rx.select(
                        items=ManageExercisesState.tag_names,
                        placeholder=LanguageState.select_tag,
                        value=ManageExercisesState.current_tag,
                        on_change=ManageExercisesState.set_current_tag,
                        multiple=True,
                    ),
                    rx.icon_button(
                        rx.icon("circle-x"),
                        on_click=ManageExercisesState.delete_tag,
                        size="2",
                        variant="ghost",
                        color_scheme="red",
                        spacing="3",
                        type="button",
                        _hover={"cursor": "pointer"},
                    ),
                    spacing="3",
                    align="center",
                ),
                flex="1",
            ),
            spacing="2",
        ),
        rx.vstack(
            # a button to link the tags to the current exercise
            rx.button(
                LanguageState.link_tag_to_exercise,
                type="button",
                on_click=ManageExercisesState.add_selected_tag,
                margin_top="0.5em",
                _hover={"cursor": "pointer"},
            ),
            # show the linked tags visually
            rx.hstack(
                rx.foreach(
                    ManageExercisesState.selected_tags,
                    lambda tag: rx.badge(
                        rx.hstack(
                            rx.text(tag),
                            rx.icon(
                                "circle-x",
                                size=16,
                            ),
                            spacing="1",
                            align_items="center",
                        ),
                        on_click=ManageExercisesState.remove_selected_tag(tag),  # type: ignore
                        color_scheme="grass",
                        cursor="pointer",
                        size="3",
                        style={
                            "_hover": {
                                "background_color": "red",
                                "color": "black",
                            }
                        },
                    ),
                ),
                margin_top="0.5em",
                margin_bottom="0.5em",
            ),
        ),
    )


def add_edit_exercise_form(mode: DialogMode) -> Sequence[rx.Component]:
    """Button for adding or editing exercises."""
    return (
        # title
        rx.text(
            LanguageState.title,
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_bottom="0.5em",
        ),
        rx.input(
            default_value=rx.cond(
                mode == DialogMode.EDIT,
                ManageExercisesState.current_exercise.title,
                "",
            ),
            placeholder=LanguageState.exercise_title_placeholder,
            size="3",
            width="100%",
            type="text",
            name="title",
        ),
        # description
        rx.text(
            LanguageState.description + ":",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.text_area(
            default_value=rx.cond(
                mode == DialogMode.EDIT,
                ManageExercisesState.current_exercise.description,
                "",
            ),
            placeholder=LanguageState.description_placeholder,
            size="3",
            width="100%",
            height="150px",
            type="text",
            name="description",
        ),
        # lesson context
        rx.text(
            LanguageState.lesson_context,
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.text_area(
            placeholder=LanguageState.lesson_context_placeholder,
            value=ManageExercisesState.lesson_context,
            on_change=ManageExercisesState.set_lesson_context,
            size="3",
            width="100%",
            height="200px",
            type="text",
            name="lesson_context",
        ),
        # lesson file upload area
        pdf_upload(),
        # prompt
        select_prompt(mode),
        # hidden checkbox
        rx.hstack(
            rx.text(
                LanguageState.hide_exercise,
                size="3",
                weight="medium",
            ),
            rx.checkbox(
                checked=ManageExercisesState.current_hidden_state,
                on_change=ManageExercisesState.set_current_hidden_state,
            ),
            align="center",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        # deadline
        rx.hstack(
            rx.text(
                LanguageState.activate_deadline,
                size="3",
                weight="medium",
            ),
            rx.checkbox(
                checked=ManageExercisesState.use_deadline,
                on_change=ManageExercisesState.set_use_deadline,
            ),
            align="center",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.cond(
            ManageExercisesState.use_deadline,
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            LanguageState.deadline,
                            size="3",
                            weight="medium",
                        ),
                        rx.input(
                            value=ManageExercisesState.current_deadline,
                            on_change=ManageExercisesState.set_current_deadline,
                            type="datetime-local",
                        ),
                    ),
                    rx.vstack(
                        rx.text(
                            LanguageState.days_to_complete,
                            size="3",
                            weight="medium",
                        ),
                        rx.input(
                            placeholder="e.g. 7",
                            value=ManageExercisesState.current_days_to_complete,
                            on_change=ManageExercisesState.set_current_days_to_complete,
                            type="number",
                            step="1",
                            min="1",
                        ),
                    ),
                ),
                rx.text(LanguageState.timezone + TIME_ZONE),
            ),
        ),
        # tags
        tag_management(),
        rx.hstack(
            rx.button(
                LanguageState.cancel,
                color_scheme="red",
                _hover={"cursor": "pointer"},
                on_click=ManageExercisesState.close_dialog,
                type="button",
            ),
            rx.cond(
                mode == DialogMode.ADD,
                rx.form.submit(
                    rx.button(
                        LanguageState.add_task,
                        color_scheme="green",
                        type="submit",
                        _hover={"cursor": "pointer"},
                    ),
                    as_child=True,
                ),
                rx.form.submit(
                    rx.button(
                        LanguageState.update_task,
                        color_scheme="yellow",
                        type="submit",
                        _hover={"cursor": "pointer"},
                    ),
                    as_child=True,
                ),
            ),
            spacing="2",
            justify="end",
        ),
    )
