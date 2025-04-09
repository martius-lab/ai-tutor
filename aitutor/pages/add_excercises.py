"""Page for the teacher to add new exercises."""

import reflex as rx
import pdfplumber
import io
from sqlmodel import select, or_

from .login import require_login
from ..models import Exercise, Tag
from .sidebar import with_sidebar


class ExerciseState(rx.State):
    """State for the exercises page."""

    exercises: list[Exercise] = []
    tag_list: list[Tag] = []
    tag_names: list[str] = []  # the tag.names as a str
    search_value: str = ""
    current_tag: str = ""  # the currently selected tag from the select window
    current_exercise: Exercise = Exercise()
    selected_tags: list[str] = []  # List to store selected tags temporarily
    lesson_file: str = ""  # the lesson file as a string
    lesson_file_name: str = ""  # name of the PDF

    @rx.event
    async def extract_lesson_material(self, files: list[rx.UploadFile]):
        """Extract the lesson material as text."""
        for file in files:
            upload_data = await file.read()
            # extract text from PDF
            with pdfplumber.open(io.BytesIO(upload_data)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()

            # remove line breaks and double spaces
            text = " ".join(text.replace("\n", " ").split())

            # save PDF text in lesson_file
            self.lesson_file = text
            # save PDF name
            self.lesson_file_name = file.name or "<unnamed file>"

    def set_current_tag(self, tag: str):
        """Set the current tag."""
        self.current_tag = tag

    def add_selected_tag(self):
        """Add the currently selected tag to the list of selected tags."""
        if not self.current_tag:
            return rx.window_alert("Select a tag first.")
        if self.current_tag and self.current_tag not in self.selected_tags:
            self.selected_tags.append(self.current_tag)
            # reset current tag after adding
            self.current_tag = ""

    def remove_selected_tag(self, tag: str):
        """Remove a tag from the list of selected tags."""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)

    def submit_exercise(self, form_data: dict):
        """Add exercises to db."""
        with rx.session() as session:
            # check if title is empty
            if not form_data["title"]:
                return rx.window_alert("Please enter a title for the exercise.")

            # check if PDF has been selected
            if self.lesson_file == "":
                return rx.window_alert(
                    "No lesson file was selected. Please upload lesson file."
                )

            # create instance and fill its fields
            new_exercise = Exercise()
            new_exercise.title = form_data["title"]
            new_exercise.description = form_data["description"]
            # use the selected tags
            new_exercise.tags = list(self.selected_tags)
            # add prompt element
            new_exercise.prompt = (
                "You will act as a learning assistant. The university student is"
                " given this exercise-title: - "
                + form_data["title"]
                + " - and this task-description: - "
                + form_data["description"]
                + " - This extracted-pdf was uploaded by the teacher as a theoretical"
                " basis for this exercise: - "
                + self.lesson_file
                + " - Analyze the answers of the student based on these * rules:"
                " * Ask rhetorical questions from time to time which indicate that the"
                " students answer is not fully correct "
                "in order to guide them in the right direction. if the student"
                " persists that their answer is right, correct them."
                " * ask relevant questions if the student acts unsure."
                " * Always be constructive and pedagogically valuable."
                " * Try to give the student a score at the end (e.g. 7/10)"
                " and some feedback."
            )
            # add exercises to db
            session.add(new_exercise)
            session.commit()
            # reload exercises
            self.load_exercises()
            # clear fields after submission
            self.selected_tags = []
            self.lesson_file = ""
            self.lesson_file_name = ""

        return rx.toast.success(
            "Exercise has been added.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    def search_exercises(self, search_value):
        """Search for a specific exercise."""
        self.search_value = search_value
        self.load_exercises()

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

    def load_tags(self):
        """Get tags from db."""
        with rx.session() as session:
            # load tags
            query_tags = select(Tag)
            self.tag_list = list(session.exec(query_tags).all())
            self.tag_names = [tag.name for tag in self.tag_list]

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

            return rx.toast.success(
                "Tag has been added and can now be selected.",
                duration=2500,
                position="bottom-center",
                invert=True,
            )

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

    def unstage_lesson_file(self):
        """Unstage the lesson file."""
        # reset lesson variables
        self.lesson_file = ""
        self.lesson_file_name = ""

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

    def get_exercise(self, exercise: Exercise):
        """Get an exercise from the db."""
        self.current_exercise = exercise
        with rx.session() as session:
            # load exercise object from db
            _exercise = session.exec(
                select(Exercise).where(Exercise.id == self.current_exercise.id)
            ).one()
        # save Tags in selected_tags
        self.selected_tags = _exercise.tags.copy() if _exercise.tags else []


def add_exercise_button() -> rx.Component:
    """Button for adding new exercises."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("file-plus", size=26),
                rx.text("Add Exercise", size="4"),
                size="3",
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
                # lesson file upload area
                rx.text(
                    "Upload lesson material (PDF): ",
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
                    on_drop=ExerciseState.extract_lesson_material(
                        rx.upload_files(upload_id="upload1")
                    ),
                ),
                # show file icon with file name
                rx.cond(
                    ExerciseState.lesson_file_name,
                    rx.box(
                        rx.hstack(
                            rx.icon("file-text", size=25),
                            rx.text(ExerciseState.lesson_file_name, color="green"),
                            rx.icon_button(
                                rx.icon("circle-x"),
                                on_click=ExerciseState.unstage_lesson_file(),  # type: ignore
                                size="2",
                                variant="ghost",
                                color_scheme="red",
                                spacing="3",
                                type="button",
                            ),
                        ),
                        padding_top="1.5em",
                    ),
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
                                items=ExerciseState.tag_names,
                                placeholder="Select a tag here",
                                value=ExerciseState.current_tag,
                                on_change=ExerciseState.set_current_tag,
                                multiple=True,
                            ),
                            rx.icon_button(
                                rx.icon("circle-x"),
                                on_click=ExerciseState.delete_tag,
                                size="2",
                                variant="ghost",
                                color_scheme="red",
                                spacing="3",
                                type="button",
                            ),
                            spacing="3",
                        ),
                        flex="1",
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                        ),
                    ),
                    rx.form.submit(
                        rx.dialog.close(
                            rx.button(
                                "Add Task",
                                color_scheme="grass",
                                type="submit",
                            ),
                            as_child=True,
                        ),
                        padding_bottom="0.5em",
                    ),
                    spacing="2",
                ),
                rx.vstack(
                    # a button to link the tags to the current exercise
                    rx.button(
                        "Link Tag To Exercise",
                        type="button",
                        on_click=ExerciseState.add_selected_tag,
                        margin_top="0.5em",
                    ),
                    # show the linked tags visually
                    rx.hstack(
                        rx.foreach(
                            ExerciseState.selected_tags,
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
                                on_click=lambda: ExerciseState.remove_selected_tag(tag),  # type: ignore
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
                # load new tags
                on_mount=ExerciseState.load_tags,
                # submit new exercises
                on_submit=ExerciseState.submit_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
            # add new tags
            tag_dialog(),
        ),
    )


def tag_dialog():
    """Dialog for adding new tags."""
    return (
        rx.dialog.root(
            rx.dialog.trigger(
                rx.button(
                    "New Selectable Tags",
                    margin_top="0.5em",
                    color_scheme="orange",
                    shade="7",
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
                            ),
                        ),
                        rx.form.submit(
                            rx.dialog.close(
                                rx.button(
                                    "Add Tag",
                                    color_scheme="grass",
                                    type="submit",
                                ),
                            ),
                        ),
                        padding_top="1em",
                        spacing="2",
                    ),
                    # submit new tags
                    on_submit=ExerciseState.submit_tag,
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
                    rx.icon_button(
                        rx.icon("circle-x"),
                        on_click=lambda: ExerciseState.delete_exercise(exercise.id),  # type: ignore
                        size="2",
                        variant="ghost",
                        color_scheme="red",
                    ),
                    edit_exercise(exercise),
                ),
                padding_left="1em",
            ),
        ),
        style={"_hover": {"bg": rx.color("gray", 3)}},
        align="center",
    )


def edit_exercise(exercise: Exercise):
    """Edit exercises on page."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("wrench", size=22),
                color_scheme="orange",
                size="2",
                variant="ghost",
                on_click=lambda: ExerciseState.get_exercise(exercise),  # type: ignore
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
                                items=ExerciseState.tag_names,
                                placeholder="Select a tag here",
                                value=ExerciseState.current_tag,
                                on_change=ExerciseState.set_current_tag,
                                multiple=True,
                            ),
                        ),
                        flex="1",
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                        ),
                    ),
                    rx.form.submit(
                        rx.dialog.close(
                            rx.button(
                                "Update Task",
                                color_scheme="yellow",
                                type="submit",
                            ),
                            as_child=True,
                        ),
                        padding_bottom="0.5em",
                    ),
                    spacing="2",
                ),
                rx.vstack(
                    # a button to link the tags to the current exercise
                    rx.button(
                        "Link Tag To Exercise",
                        type="button",
                        on_click=ExerciseState.add_selected_tag,
                        margin_top="0.5em",
                    ),
                    # show the linked tags visually
                    rx.hstack(
                        rx.foreach(
                            ExerciseState.selected_tags,
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
                                on_click=lambda: ExerciseState.remove_selected_tag(tag),  # type: ignore
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
                # load tags
                on_mount=ExerciseState.load_tags,
                # update exercise
                on_submit=ExerciseState.update_exercise,
                reset_on_submit=False,
                enter_key_submit=True,
            ),
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
                        on_change=lambda value: ExerciseState.search_exercises(value),
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
                rx.table.body(rx.foreach(ExerciseState.exercises, show_exercise)),
                on_mount=ExerciseState.load_exercises,
                variant="surface",
                size="3",
                width="85vw",
                overflow_y="auto",
                max_height="70vh",
            ),
        ),
    )


@with_sidebar
@require_login(role="teacher")
def add_exercises_default() -> rx.Component:
    """Add exercises page."""
    return rx.center(
        rx.color_mode.button(position="top-right", type="button"),
        rx.vstack(
            rx.center(
                rx.heading("Exercises", size="8", padding_top="2em"),
                padding_bottom="2em",
                width="100%",
            ),
            exercise_table(),
        ),
    )
