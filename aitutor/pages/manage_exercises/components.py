"""The Components for the manage exercises page."""

import reflex as rx
from enum import Enum

from aitutor.models import Exercise
from aitutor.pages.manage_exercises.state import ManageExercisesState


class Mode(Enum):
    """Enum for the mode of the add/edit function."""

    ADD = "add"
    EDIT = "edit"


def new_tag_dialog():
    """Dialog for adding new tags."""
    return (
        rx.dialog.root(
            rx.dialog.trigger(
                rx.button(
                    "Create New Tag",
                    margin_top="0.5em",
                    color_scheme="orange",
                    shade="7",
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.dialog.content(
                rx.form(
                    rx.text("Name", padding_bottom="0.5em"),
                    rx.input(
                        placeholder="Enter a new tag here. "
                        "It can be selected afterwards.",
                        name="tag",
                    ),
                    rx.center(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                color_scheme="red",
                                type="button",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        rx.form.submit(
                            rx.button(
                                "Add Tag",
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
            on_open_change=ManageExercisesState.set_add_tag_dialog_is_open,  # type: ignore
        ),
    )


def delete_exercise_button(exercise: Exercise):
    """Delete exercise"""
    return (
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.icon_button(
                    rx.icon("circle-x"),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("Delete Exercise"),
                rx.alert_dialog.description(
                    "Are you sure you want to delete this exercise?"
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Confirm",
                            color_scheme="iris",
                            on_click=lambda: ManageExercisesState.delete_exercise(
                                exercise.id
                            ),  # type: ignore
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
        rx.table.cell(exercise.id),
        rx.table.cell(exercise.title, max_width="175px"),
        rx.table.cell(exercise.description, max_width="400px"),
        rx.table.cell(
            rx.flex(
                rx.foreach(
                    exercise.tags,
                    lambda tag: rx.text(tag + ","),
                ),
                wrap="wrap",
            ),
            max_width="100px",
            max_height="100px",
            overflow="auto",
            padding="1em",
        ),
        rx.table.cell(
            rx.center(
                rx.hstack(
                    delete_exercise_button(exercise),
                    edit_exercise_button(exercise),
                ),
                padding_left="1em",
            ),
        ),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def header_cell(text: str, icon: str):
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
            rx.flex(
                rx.box(
                    # search bar
                    rx.input(
                        rx.input.slot(rx.icon("search")),
                        placeholder="Search...",
                        size="3",
                        max_width="250px",
                        style={"_hover": {"bg": rx.color("gray", 2)}},
                        on_change=lambda value: ManageExercisesState.search_exercises(
                            value
                        ),
                    ),
                    flex="1",
                ),
                # the button for adding exercises
                rx.box(
                    add_exercise_button(),
                ),
                width="100%",
            ),
            # head cells for the main table
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        header_cell("ID", "file-digit"),
                        header_cell("Task", "briefcase-business"),
                        header_cell("Description", "book-open-text"),
                        header_cell("Tags", "tag"),
                        rx.table.column_header_cell("Delete | Edit", align="center"),
                    ),
                ),
                # dynamically render each new entry
                rx.table.body(
                    rx.foreach(ManageExercisesState.exercises, show_exercise)
                ),
                on_mount=ManageExercisesState.load_exercises,
                variant="surface",
                size="3",
                width="85vw",
                overflow_y="auto",
                max_height="70vh",
            ),
        ),
    )


def add_exercise_button() -> rx.Component:
    """Button for adding new exercises."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("file-plus", size=26),
                rx.text("Add Exercise", size="4"),
                size="3",
                _hover={"cursor": "pointer"},
                on_click=ManageExercisesState.reset_exercise_form,
            ),
        ),
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="file-plus", size=34),
                    color_scheme="grass",
                    radius="full",
                ),
                rx.vstack(
                    rx.dialog.title(
                        "New Exercise",
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        "add a new exercise for the students",
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
                add_edit_exercise_form(mode=Mode.ADD),
                on_mount=ManageExercisesState.load_tags,
                on_submit=ManageExercisesState.add_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            new_tag_dialog(),
        ),
        open=ManageExercisesState.add_exercise_dialog_is_open,
        on_open_change=ManageExercisesState.set_add_exercise_dialog_is_open,  # type: ignore
    )


def edit_exercise_button(exercise: Exercise):
    """Edit exercises on page."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("wrench", size=22),
                color_scheme="orange",
                size="2",
                variant="ghost",
                on_click=ManageExercisesState.load_exercise(exercise),  # type: ignore
                _hover={"cursor": "pointer"},
            ),
            padding_left="1em",
        ),
        rx.dialog.content(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="wrench", size=34),
                    color_scheme="orange",
                    radius="full",
                ),
                rx.vstack(
                    rx.dialog.title(
                        "Edit Exercise",
                        weight="bold",
                        margin="0",
                    ),
                    rx.dialog.description(
                        "Update already existing exercise",
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
                add_edit_exercise_form(mode=Mode.EDIT),
                on_mount=ManageExercisesState.load_tags,
                on_submit=ManageExercisesState.update_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            new_tag_dialog(),
        ),
        open=ManageExercisesState.edit_exercise_dialog_is_open,
        on_open_change=ManageExercisesState.set_edit_exercise_dialog_is_open,  # type: ignore
    )


def pdf_upload() -> rx.Component:
    """Upload area for lesson material in PDF format."""
    return (
        rx.text(
            "Add lesson material (PDF): ",
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
                    "Select File",
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
                    "Drag and drop or click the button to select",
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
            "Last uploaded file: ",
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


def select_prompt(mode: Mode) -> rx.Component:
    """The prompt selection component."""
    return (
        rx.text(
            "Prompt: ",
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
                placeholder="Select a Prompt here",
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
                            mode == Mode.ADD,
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
            "Tags: ",
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
                        placeholder="Select a tag here",
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
                ),
                flex="1",
            ),
            spacing="2",
        ),
        rx.vstack(
            # a button to link the tags to the current exercise
            rx.button(
                "Link Tag To Exercise",
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
                        on_click=lambda: ManageExercisesState.remove_selected_tag(  # noqa: E501
                            tag
                        ),  # type: ignore
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


def add_edit_exercise_form(mode: Mode) -> rx.Component:
    """Button for adding or editing exercises."""
    return (
        # title
        rx.text(
            "Title: ",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_bottom="0.5em",
        ),
        rx.input(
            default_value=rx.cond(
                mode == Mode.EDIT,
                ManageExercisesState.current_exercise.title,
                "",
            ),
            placeholder="Exercise title",
            size="3",
            width="100%",
            type="text",
            name="title",
        ),
        # description
        rx.text(
            "Description: ",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.text_area(
            rx.cond(
                mode == Mode.EDIT,
                ManageExercisesState.current_exercise.description,
                "",
            ),
            placeholder="Describe the task here",
            size="3",
            width="100%",
            height="150px",
            type="text",
            name="description",
        ),
        # lesson context
        rx.text(
            "Lesson Context: ",
            size="3",
            weight="medium",
            text_align="left",
            width="100%",
            padding_top="1.5em",
            padding_bottom="0.5em",
        ),
        rx.text_area(
            placeholder="Add lesson context here",
            value=ManageExercisesState.lesson_context,
            on_change=ManageExercisesState.set_lesson_context,  # type: ignore
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
        # tags
        tag_management(),
        rx.hstack(
            rx.dialog.close(
                rx.button(
                    "Cancel",
                    color_scheme="red",
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.form.submit(
                rx.cond(
                    mode == Mode.ADD,
                    rx.button(
                        "Add Task",
                        color_scheme="green",
                        type="submit",
                        _hover={"cursor": "pointer"},
                    ),
                    rx.button(
                        "Update Task",
                        color_scheme="yellow",
                        type="submit",
                        _hover={"cursor": "pointer"},
                    ),
                ),
                padding_bottom="0.5em",
            ),
            spacing="2",
            justify="end",
        ),
    )
