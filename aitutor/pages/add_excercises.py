"""Page for the teacher to add new exercises."""

import reflex as rx
import pdfplumber
import io
from sqlmodel import select, or_

from aitutor.config import get_config
from aitutor.models import Exercise, Tag
from aitutor.pages.navbar import with_navbar
from aitutor.auth.protection import require_role_at_least
from aitutor.models import UserRole


class AddExerciseState(rx.State):
    """State for the exercises page."""

    # Flags to control if dialogs are open.  They are needed as a workaround due to a
    # bug with Reflex dialogs, see
    # https://github.com/reflex-dev/reflex/issues/4221#issuecomment-2430197475
    add_exercise_dialog_is_open: bool = False
    add_tag_dialog_is_open: bool = False

    exercises: list[Exercise] = []
    tag_list: list[Tag] = []
    tag_names: list[str] = []  # the tag.names as a str
    search_value: str = ""
    current_tag: str = ""  # the currently selected tag from the select window
    current_exercise: Exercise = Exercise()
    selected_tags: list[str] = []  # List to store selected tags temporarily
    lesson_context: str = ""  # the lesson context as a string
    lesson_file_name: str = ""  # name of the PDF
    current_prompt_name: str = ""  # the current prompt name
    prompts: dict[str, str] = {}  # the prompt templates as a dict
    prompt_names: list[str] = []  # the prompt names as a list
    extracting_lesson_material: bool = (
        False  # Flag to control if lesson material is being extracted
    )

    @rx.event
    def initialize(self):
        """Initialize the state (call this in the on_load event)."""
        config = get_config()
        self.prompts = {p.name: p.prompt for p in config.exercise_prompts}
        self.prompt_names = list(self.prompts.keys())

    @rx.event
    def set_current_prompt_name(self, prompt_name: str):
        """Set the current prompt name."""
        self.current_prompt_name = prompt_name

    @rx.event
    async def extract_lesson_material(self, files: list[rx.UploadFile]):
        """Extract the lesson material as text."""
        self.extracting_lesson_material = True
        yield
        for file in files:
            upload_data = await file.read()
            # extract text from PDF
            with pdfplumber.open(io.BytesIO(upload_data)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()

            # remove line breaks and double spaces
            text = " ".join(text.replace("\n", " ").split())

            # save PDF text in lesson_context
            self.lesson_context = (
                self.lesson_context
                + "\n\n―――――――――――――――――――――――――――――――――\n"
                + text
                + "\n―――――――――――――――――――――――――――――――――\n\n"
            )
            # save PDF name
            self.lesson_file_name = file.name or "<unnamed file>"
        self.extracting_lesson_material = False
        yield

    @rx.event
    def set_current_tag(self, tag: str):
        """Set the current tag."""
        self.current_tag = tag

    @rx.event
    def add_selected_tag(self):
        """Add the currently selected tag to the list of selected tags."""
        if not self.current_tag:
            return rx.window_alert("Select a tag first.")
        if self.current_tag and self.current_tag not in self.selected_tags:
            self.selected_tags.append(self.current_tag)
            # reset current tag after adding
            self.current_tag = ""

    @rx.event
    def remove_selected_tag(self, tag: str):
        """Remove a tag from the list of selected tags."""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)

    @rx.event
    def submit_exercise(self, form_data: dict):
        """Add exercises to db."""
        with rx.session() as session:
            # check if title is empty
            if not form_data["title"]:
                return rx.window_alert("Please enter a title for the exercise.")

            # create instance and fill its fields
            new_exercise = Exercise(
                lesson_context=self.lesson_context,
            )
            new_exercise.title = form_data["title"]
            new_exercise.description = form_data["description"]
            # use the selected tags
            new_exercise.tags = list(self.selected_tags)
            # add prompt element
            if self.current_prompt_name == "":
                return rx.window_alert(
                    "Please select a prompt template for the exercise."
                )
            new_exercise.prompt = self.prompts[self.current_prompt_name].format(
                title=form_data["title"],
                description=form_data["description"],
                lesson_context=self.lesson_context,
            )
            new_exercise.prompt_name = self.current_prompt_name
            # add exercises to db
            session.add(new_exercise)
            session.commit()
            # reload exercises
            self.load_exercises()
            # clear fields after submission
            self.selected_tags = []
            self.lesson_context = ""
            self.lesson_file_name = ""

            self.add_exercise_dialog_is_open = False

        return rx.toast.success(
            "Exercise has been added.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def search_exercises(self, search_value):
        """Search for a specific exercise."""
        self.search_value = search_value
        self.load_exercises()

    @rx.event
    def load_exercises(self):
        """Get exercises from db."""
        with rx.session() as session:
            # load exercises
            query_exercises = select(Exercise)
            # search for distinct entries
            if self.search_value:
                search_value = f"%{str(self.search_value).lower()}%"
                query_exercises = query_exercises.where(
                    or_(
                        *[
                            getattr(Exercise, field).ilike(search_value)
                            for field in Exercise.get_fields()
                        ],
                    )
                )
            self.exercises = list(session.exec(query_exercises).all())

    @rx.event
    def load_tags(self):
        """Get tags from db."""
        with rx.session() as session:
            # load tags
            query_tags = select(Tag)
            self.tag_list = list(session.exec(query_tags).all())
            self.tag_names = [tag.name for tag in self.tag_list]

    @rx.event
    def submit_tag(self, form_data: dict):
        """Add tags to db."""
        with rx.session() as session:
            # check if tag is not None
            if form_data["tag"] == "":
                return rx.window_alert("Please enter a tag name.")

            # check if tag exists
            existing_tag = session.exec(
                select(Tag).where(Tag.name == form_data["tag"])
            ).one_or_none()
            if existing_tag is not None:
                return rx.window_alert("Tag exists already.")

            new_tag = Tag(name=form_data["tag"])
            # add tag to db
            session.add(new_tag)
            session.commit()
            self.load_tags()

            self.add_tag_dialog_is_open = False

            return rx.toast.success(
                "Tag has been added and can now be selected.",
                duration=2500,
                position="bottom-center",
                invert=True,
            )

    @rx.event
    def update_exercise(self, form_data: dict):
        """Update exercises in db."""
        with rx.session() as session:
            updated_exercise = session.exec(
                select(Exercise).where(Exercise.id == self.current_exercise.id)
            ).one()
            # update fields
            updated_exercise.title = form_data["title"]
            updated_exercise.description = form_data["description"]
            updated_exercise.tags = self.selected_tags
            updated_exercise.prompt = self.prompts[self.current_prompt_name].format(
                title=form_data["title"],
                description=form_data["description"],
                lesson_context=self.lesson_context,
            )
            updated_exercise.prompt_name = self.current_prompt_name
            updated_exercise.lesson_context = self.lesson_context

            session.add(updated_exercise)
            session.commit()
            self.load_exercises()

        # reset selected tags
        self.selected_tags = []

        return rx.toast.success(
            "Exercise updated successfully.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def delete_tag(self):
        """Delete a tag from the db."""
        with rx.session() as session:
            # fetch the tag by its name
            tag_to_delete = session.exec(
                select(Tag).where(Tag.name == self.current_tag)
            ).first()

            # no tag selected
            if tag_to_delete is None:
                return rx.window_alert("Tag not found. Please select a tag.")

            # check if the tag has a valid id
            if tag_to_delete.id is None:
                return rx.window_alert("Tag has no valid id.")

            # reset current tag, so that placeholder text reappears
            self.current_tag = ""

            # If tag is found and has a valid id, delete it
            session.delete(tag_to_delete)
            session.commit()
            # reload tags
            self.load_tags()

            return rx.toast.success(
                "Tag has been deleted",
                duration=2500,
                position="bottom-center",
                invert=True,
            )

    def delete_exercise(self, id: int):
        """Delete an exercise from the db."""
        with rx.session() as session:
            exercise = session.exec(select(Exercise).where(Exercise.id == id)).first()
            session.delete(exercise)
            session.commit()
        self.load_exercises()

        return rx.toast.success(
            "Exercise has been deleted.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    def load_exercise(self, exercise: Exercise):
        """Get an exercise from the db."""
        self.current_exercise = exercise
        with rx.session() as session:
            # load exercise object from db
            _exercise = session.exec(
                select(Exercise).where(Exercise.id == self.current_exercise.id)
            ).one()
        self.current_prompt_name = _exercise.prompt_name
        self.lesson_context = _exercise.lesson_context
        # save Tags in selected_tags
        self.selected_tags = _exercise.tags.copy() if _exercise.tags else []
        # reset lesson_file_name
        self.lesson_file_name = ""

    @rx.event
    def reset_exercise_form(self):
        """Reset the exercise form."""
        self.lesson_context = ""
        self.lesson_file_name = ""
        self.selected_tags = []
        self.current_prompt_name = ""
        self.current_tag = ""


def add_exercise_button() -> rx.Component:
    """Button for adding new exercises."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("file-plus", size=26),
                rx.text("Add Exercise", size="4"),
                size="3",
                _hover={"cursor": "pointer"},
                on_click=AddExerciseState.reset_exercise_form,
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
                    value=AddExerciseState.lesson_context,
                    on_change=AddExerciseState.set_lesson_context,  # type: ignore
                    size="3",
                    width="100%",
                    height="200px",
                    type="text",
                    name="lesson_context",
                ),
                # lesson file upload area
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
                                AddExerciseState.extracting_lesson_material,
                                {"cursor": "not-allowed"},
                                {"cursor": "pointer"},
                            ),
                            loading=AddExerciseState.extracting_lesson_material,
                            disabled=AddExerciseState.extracting_lesson_material,
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
                    on_drop=AddExerciseState.extract_lesson_material(
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
                    AddExerciseState.lesson_file_name,
                    rx.box(
                        rx.hstack(
                            rx.icon("file-text", size=25),
                            rx.text(AddExerciseState.lesson_file_name, color="green"),
                        ),
                    ),
                ),
                # prompt
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
                        items=AddExerciseState.prompt_names,
                        placeholder="Select a Prompt here",
                        value=AddExerciseState.current_prompt_name,
                        on_change=AddExerciseState.set_current_prompt_name,
                        multiple=True,
                    ),
                    # hover to show the promot
                    rx.popover.root(
                        rx.popover.trigger(
                            rx.icon("info", size=20),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.popover.content(
                            rx.flex(
                                rx.text(
                                    AddExerciseState.prompts[
                                        AddExerciseState.current_prompt_name
                                    ],
                                    padding="1em",
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
                                items=AddExerciseState.tag_names,
                                placeholder="Select a tag here",
                                value=AddExerciseState.current_tag,
                                on_change=AddExerciseState.set_current_tag,
                                multiple=True,
                            ),
                            rx.icon_button(
                                rx.icon("circle-x"),
                                on_click=AddExerciseState.delete_tag,
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
                        on_click=AddExerciseState.add_selected_tag,
                        margin_top="0.5em",
                        _hover={"cursor": "pointer"},
                    ),
                    # show the linked tags visually
                    rx.hstack(
                        rx.foreach(
                            AddExerciseState.selected_tags,
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
                                on_click=lambda: AddExerciseState.remove_selected_tag(
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
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.form.submit(
                        rx.button(
                            "Add Task",
                            color_scheme="grass",
                            type="submit",
                            _hover={"cursor": "pointer"},
                        ),
                        padding_bottom="0.5em",
                    ),
                    spacing="2",
                    justify="end",
                ),
                # load new tags
                on_mount=AddExerciseState.load_tags,
                # submit new exercises
                on_submit=AddExerciseState.submit_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            tag_dialog(),
        ),
        open=AddExerciseState.add_exercise_dialog_is_open,
        on_open_change=AddExerciseState.set_add_exercise_dialog_is_open,  # type: ignore
    )


def tag_dialog():
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
                    on_submit=AddExerciseState.submit_tag,
                ),
            ),
            open=AddExerciseState.add_tag_dialog_is_open,
            on_open_change=AddExerciseState.set_add_tag_dialog_is_open,  # type: ignore
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
                            on_click=lambda: AddExerciseState.delete_exercise(
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


def edit_exercise_button(exercise: Exercise):
    """Edit exercises on page."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("wrench", size=22),
                color_scheme="orange",
                size="2",
                variant="ghost",
                on_click=AddExerciseState.load_exercise(exercise),  # type: ignore
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
                    default_value=exercise.title,
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
                    exercise.description,
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
                    value=AddExerciseState.lesson_context,
                    on_change=AddExerciseState.set_lesson_context,  # type: ignore
                    size="3",
                    width="100%",
                    height="200px",
                    type="text",
                    name="lesson_context",
                ),
                # lesson file upload area
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
                                AddExerciseState.extracting_lesson_material,
                                {"cursor": "not-allowed"},
                                {"cursor": "pointer"},
                            ),
                            loading=AddExerciseState.extracting_lesson_material,
                            disabled=AddExerciseState.extracting_lesson_material,
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
                    on_drop=AddExerciseState.extract_lesson_material(
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
                    AddExerciseState.lesson_file_name,
                    rx.box(
                        rx.hstack(
                            rx.icon("file-text", size=25),
                            rx.text(AddExerciseState.lesson_file_name, color="green"),
                        ),
                    ),
                ),
                # prompt
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
                        items=AddExerciseState.prompt_names,
                        placeholder=AddExerciseState.current_prompt_name,
                        value=AddExerciseState.current_prompt_name,
                        on_change=AddExerciseState.set_current_prompt_name,
                        multiple=True,
                    ),
                    # hover to show the promot
                    rx.popover.root(
                        rx.popover.trigger(
                            rx.icon("info", size=20),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.popover.content(
                            rx.flex(
                                rx.text(
                                    # show the prompt from the db or
                                    # the selected prompt template
                                    rx.cond(
                                        AddExerciseState.current_exercise.prompt_name
                                        == AddExerciseState.current_prompt_name,
                                        AddExerciseState.current_exercise.prompt,
                                        AddExerciseState.prompts[
                                            AddExerciseState.current_prompt_name
                                        ],
                                    ),
                                    padding="1em",
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
                                items=AddExerciseState.tag_names,
                                placeholder="Select a tag here",
                                value=AddExerciseState.current_tag,
                                on_change=AddExerciseState.set_current_tag,
                                multiple=True,
                            ),
                            rx.icon_button(
                                rx.icon("circle-x"),
                                on_click=AddExerciseState.delete_tag,
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
                        on_click=AddExerciseState.add_selected_tag,
                        margin_top="0.5em",
                        _hover={"cursor": "pointer"},
                    ),
                    # show the linked tags visually
                    rx.hstack(
                        rx.foreach(
                            AddExerciseState.selected_tags,
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
                                on_click=lambda: AddExerciseState.remove_selected_tag(
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
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.form.submit(
                        rx.dialog.close(
                            rx.button(
                                "Update Task",
                                color_scheme="yellow",
                                type="submit",
                                _hover={"cursor": "pointer"},
                            ),
                            as_child=True,
                        ),
                        padding_bottom="0.5em",
                    ),
                    spacing="2",
                    justify="end",
                ),
                # load tags
                on_mount=AddExerciseState.load_tags,
                # update exercise
                on_submit=AddExerciseState.update_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tag
            tag_dialog(),
        ),
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
                        on_change=lambda value: AddExerciseState.search_exercises(
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
                rx.table.body(rx.foreach(AddExerciseState.exercises, show_exercise)),
                on_mount=AddExerciseState.load_exercises,
                variant="surface",
                size="3",
                width="85vw",
                overflow_y="auto",
                max_height="70vh",
            ),
        ),
    )


@with_navbar
@require_role_at_least(UserRole.ADMIN)
def add_exercises_default() -> rx.Component:
    """Add exercises page."""
    return rx.center(
        rx.vstack(
            rx.center(
                rx.heading("Exercises", size="8", padding_top="2em"),
                padding_bottom="2em",
                width="100%",
            ),
            exercise_table(),
        ),
    )
