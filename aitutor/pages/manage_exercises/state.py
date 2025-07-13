"""The state for the manage exercises page."""

import reflex as rx
import pdfplumber
import io
from enum import Enum
from sqlmodel import select, or_

from aitutor.models import Exercise, Tag, UserRole
from aitutor.auth.state import SessionState
from aitutor.config import get_config
from aitutor.auth.protection import state_require_role_at_least


class DialogMode(Enum):
    """Enum for the mode of the add/edit function."""

    ADD = "add"
    EDIT = "edit"


class ManageExercisesState(SessionState):
    """State for the exercises page."""

    # Flags to control if dialogs are open.  They are needed as a workaround due to a
    # bug with Reflex dialogs, see
    # https://github.com/reflex-dev/reflex/issues/4221#issuecomment-2430197475
    add_exercise_dialog_is_open: bool = False
    edit_exercise_dialog_is_open: bool = False
    add_tag_dialog_is_open: bool = False

    exercises: list[Exercise] = []
    tag_list: list[Tag] = []
    tag_names: list[str] = []
    search_value: str = ""
    #: the currently selected tag from the select window
    current_tag: str = ""
    #: the current exercise to be edited
    current_exercise: Exercise = Exercise()
    #: List to store selected tags temporarily
    selected_tags: list[str] = []
    #: the lesson context from the form
    lesson_context: str = ""
    #: name of the extracted PDF
    lesson_file_name: str = ""
    #: the currently selected prompt name
    current_prompt_name: str = ""
    #: the prompt templates
    prompts: dict[str, str] = {}
    #: the prompt names that can be selected
    prompt_names: list[str] = []
    #: Flag to control if lesson material is being extracted
    extracting_lesson_material: bool = False
    #: Flag to control if the current exercise is hidden
    current_hidden_state: bool = False

    @rx.event
    @state_require_role_at_least(UserRole.ADMIN)
    def on_load(self):
        """Initialize the state"""

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
    def add_exercise(self, form_data: dict):
        """Add exercises to db."""
        with rx.session() as session:
            # check if title is empty
            if not form_data["title"]:
                return rx.window_alert("Please enter a title for the exercise.")
            if not form_data["description"]:
                return rx.window_alert("Please enter a description for the exercise.")
            if self.lesson_context == "":
                return rx.window_alert(
                    "Please add some lesson context to the exercise."
                )
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
            new_exercise.is_hidden = self.current_hidden_state
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
            self.exercises = list(
                session.exec(query_exercises.order_by(Exercise.id.desc())).all()  # type: ignore
            )

    @rx.event
    def load_tags(self):
        """Get tags from db."""
        with rx.session() as session:
            # load tags
            query_tags = select(Tag)
            self.tag_list = list(session.exec(query_tags).all())
            self.tag_names = [tag.name for tag in self.tag_list]

    @rx.event
    def toggle_visibility(self, exercise: Exercise):
        """Toggle the visibility of an exercise."""
        with rx.session() as session:
            # load exercise object from db
            _exercise = session.exec(
                select(Exercise).where(Exercise.id == exercise.id)
            ).one()
            # toggle visibility
            _exercise.is_hidden = not _exercise.is_hidden
            session.commit()
            # update the is_hidden field of the exercise in the state
            for i, e in enumerate(self.exercises):
                if e.id == exercise.id:
                    self.exercises[i].is_hidden = _exercise.is_hidden
                    break

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
        self.edit_exercise_dialog_is_open = False

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
            updated_exercise.is_hidden = self.current_hidden_state

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

    @rx.event
    def reset_exercise_form(self):
        """Reset the exercise form."""
        self.lesson_context = ""
        self.lesson_file_name = ""
        self.selected_tags = []
        self.current_prompt_name = ""
        self.current_tag = ""
        self.current_hidden_state = False

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
        """load the exercise into the state variables."""
        self.current_exercise = exercise
        self.current_prompt_name = exercise.prompt_name
        self.lesson_context = exercise.lesson_context
        self.selected_tags = exercise.tags.copy() if exercise.tags else []
        self.lesson_file_name = ""  # reset lesson_file_name
        self.current_hidden_state = exercise.is_hidden

    @rx.event
    def open_add_dialog(self):
        """Open the add/edit dialog."""
        self.reset_exercise_form()
        self.add_exercise_dialog_is_open = True

    @rx.event
    def open_edit_dialog(self, exercise: Exercise):
        """Open the edit dialog for an exercise."""
        self.load_exercise(exercise)
        self.edit_exercise_dialog_is_open = True

    @rx.event
    def close_dialog(self):
        """Close the add/edit dialog."""
        self.add_exercise_dialog_is_open = False
        self.edit_exercise_dialog_is_open = False

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises = []
        self.tag_list = []
        self.tag_names = []
        self.search_value = ""
        self.current_tag = ""
        self.current_exercise = Exercise()
        self.selected_tags = []
        self.lesson_context = ""
        self.lesson_file_name = ""
        self.current_prompt_name = ""
        self.prompts = {}
        self.prompt_names = []
        self.extracting_lesson_material = False
        self.current_hidden_state = False
