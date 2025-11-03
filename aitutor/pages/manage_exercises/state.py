"""The state for the manage exercises page."""

import reflex as rx
import pdfplumber
import io
import json
from typing import override
from enum import Enum
from sqlmodel import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from aitutor.models import Exercise, Tag, UserRole
from aitutor.auth.state import SessionState
from aitutor.utilities.filtering_components import FilterMixin
from aitutor.config import get_config
from aitutor.auth.protection import state_require_role_at_least
import aitutor.global_vars as gv
from aitutor.language_state import BackendTranslations as BT


class DialogMode(Enum):
    """Enum for the mode of the add/edit function."""

    ADD = "add"
    EDIT = "edit"


class ManageExercisesState(FilterMixin, SessionState):
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
    # valid search keys. overrides the var from FilterMixin
    search_keys: list[str] = [gv.SEARCH_EXERCISE_KEY, gv.SEARCH_TAG_KEY]
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
    #: the current deadline
    current_deadline: str = ""
    #: days to complete the exercise
    current_days_to_complete: str = ""
    #: flag to control if the exercise should have a deadline
    use_deadline: bool = True

    # These dictionarys are needed because reflex does not accept propertys like
    # exercise.is_started or exercise.editing_period in the components.
    # So this is a workaround.
    #: dictionary to store editing periods for exercises. Key is exercise id.
    editing_periods: dict[int, str] = {}
    #: dictionary to store which exercises are started. Key is exercise id.
    exercise_is_started: dict[int, bool] = {}
    #: dictionary to store which exercises are selected. Key is exercise id.
    exercise_is_selected: dict[int, bool] = {}

    @rx.event
    def set_add_tag_dialog_is_open(self, is_open: bool):
        """Set the add tag dialog is open flag."""
        self.add_tag_dialog_is_open = is_open

    @rx.event
    def set_current_tag(self, tag: str):
        """Set the current tag."""
        self.current_tag = tag

    @rx.event
    def set_lesson_context(self, context: str):
        """Set the lesson context."""
        self.lesson_context = context

    @rx.event
    def set_current_prompt_name(self, prompt_name: str):
        """Set the current prompt name."""
        self.current_prompt_name = prompt_name

    @rx.event
    def set_current_hidden_state(self, hidden: bool):
        """Set the current hidden state."""
        self.current_hidden_state = hidden

    @rx.event
    def set_current_deadline(self, deadline: str):
        """Set the current deadline."""
        self.current_deadline = deadline

    @rx.event
    def set_current_days_to_complete(self, days: str):
        """Set the current days to complete."""
        self.current_days_to_complete = days

    @rx.event
    def set_use_deadline(self, use: bool):
        """Set the use_deadline flag."""
        self.use_deadline = use

    @rx.event
    def set_all_exercises_selected(self, is_selected: bool):
        """Set all exercises as selected or unselected."""
        for exercise in self.exercises:
            self.exercise_is_selected[exercise.id] = is_selected  # type: ignore

    @rx.event
    def set_exercise_is_selected(self, exercise_id: int | None, is_selected: bool):
        """Set the exercise_is_selected flag."""
        self.exercise_is_selected[exercise_id] = is_selected  # type: ignore

    @rx.event
    @state_require_role_at_least(UserRole.ADMIN)
    def on_load(self):
        """Initialize the state"""

        self.global_load()
        config = get_config()
        self.prompts = {p.name: p.prompt for p in config.exercise_prompts}
        self.prompt_names = list(self.prompts.keys())
        self.load_exercises()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.exercises = []
        self.tag_list = []
        self.tag_names = []
        self.search_values = []  # from FilterMixin
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
        self.current_deadline = ""
        self.current_days_to_complete = ""
        self.use_deadline = True
        self.editing_periods = {}
        self.exercise_is_started = {}
        self.exercise_is_selected = {}

    @rx.var
    def all_exercises_selected(self) -> bool:
        """Return True if all exercises are selected."""
        return all(self.exercise_is_selected.values())

    @rx.var
    def something_is_selected(self) -> bool:
        """Return True if at least one exercise is selected."""
        return any(self.exercise_is_selected.values())

    @rx.event
    def delete_selected_exercises(self):
        """Delete all selected exercises."""
        ids_to_delete = [
            exercise_id
            for exercise_id, is_selected in self.exercise_is_selected.items()
            if is_selected
        ]
        for exercise_id in ids_to_delete:
            self.delete_exercise(exercise_id)

        yield rx.toast.success(
            BT.selected_exercises_deleted(self.language),
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def export_selected_exercises(self):
        """Export all selected exercises as JSON string."""
        exercises_to_export = [
            exercise
            for exercise in self.exercises
            if self.exercise_is_selected[exercise.id]  # type: ignore
        ]
        exercises_dicts = []
        for ex in exercises_to_export:
            exercises_dicts.append(
                {
                    "title": ex.title,
                    "description": ex.description,
                    "lesson_context": ex.lesson_context,
                    "prompt_name": ex.prompt_name,
                    "deadline": ex.deadline.isoformat() if ex.deadline else None,
                    "days_to_complete": ex.days_to_complete,
                    "tags": [tag.name for tag in ex.tags],
                }
            )

        json_data = json.dumps(exercises_dicts, indent=4)
        timestamp = datetime.today().date().isoformat()

        return rx.download(
            data=json_data, filename=f"aitutor-exercises-{timestamp}.json"
        )

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
            if self.current_prompt_name == "":
                return rx.window_alert(
                    "Please select a prompt template for the exercise."
                )
            new_exercise = Exercise(
                lesson_context=self.lesson_context,
                title=form_data["title"],
                description=form_data["description"],
                prompt=self.prompts[self.current_prompt_name].format(
                    title=form_data["title"],
                    description=form_data["description"],
                    lesson_context=self.lesson_context,
                ),
                prompt_name=self.current_prompt_name,
                is_hidden=self.current_hidden_state,
                tags=session.exec(
                    select(Tag).where(Tag.name.in_(self.selected_tags))  # type: ignore
                ).all(),
            )
            # set deadline and days to complete
            alert, deadline, days_to_complete = self.get_deadline_and_days_to_complete()
            # alert the user if no values were provided
            if alert:
                return alert
            new_exercise.deadline = (
                datetime.fromisoformat(deadline) if deadline else None
            )
            new_exercise.days_to_complete = days_to_complete

            session.add(new_exercise)
            session.commit()
            self.load_exercises()
            self.selected_tags = []
            self.lesson_context = ""
            self.lesson_file_name = ""
            self.add_exercise_dialog_is_open = False

        return rx.toast.success(
            BT.exercise_added(self.language),
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    @override
    @rx.event
    def load_filtered_data(self):
        """implements the abstract method from FilterMixin"""
        self.load_exercises()

    def load_exercises(self):
        """Get exercises from db."""
        with rx.session() as session:
            # load exercises
            query_exercises = select(Exercise).options(selectinload(Exercise.tags))  # type: ignore

            # filter with search values
            if self.search_values:
                search_conditions = []
                for key, value in self.search_values:
                    match key:
                        case gv.SEARCH_EXERCISE_KEY:
                            search_conditions.append(Exercise.title.ilike(f"%{value}%"))  # type: ignore
                        case gv.SEARCH_TAG_KEY:
                            search_conditions.append(
                                Exercise.tags.any(Tag.name.ilike(f"%{value}%"))  # type: ignore
                            )
                        case _:
                            search_conditions.append(
                                or_(
                                    Exercise.title.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.description.ilike(f"%{value}%"),  # type: ignore
                                    Exercise.tags.any(Tag.name.ilike(f"%{value}%")),  # type: ignore
                                )
                            )
                query_exercises = query_exercises.where(and_(*search_conditions))

            # get exercises from db and order by id descending
            self.exercises = list(
                session.exec(query_exercises.order_by(Exercise.id.desc())).all()  # type: ignore
            )

        # fill dictionarys with correct values for the currently loaded exercises
        self.editing_periods = {
            e.id: e.editing_period for e in self.exercises if e.id is not None
        }
        self.exercise_is_started = {
            e.id: e.is_started for e in self.exercises if e.id is not None
        }
        self.exercise_is_selected = {
            e.id: False for e in self.exercises if e.id is not None
        }

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
                BT.tag_was_added(self.language),
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
            updated_exercise.tags = session.exec(
                select(Tag).where(Tag.name.in_(self.selected_tags))  # type: ignore
            ).all()
            updated_exercise.prompt = self.prompts[self.current_prompt_name].format(
                title=form_data["title"],
                description=form_data["description"],
                lesson_context=self.lesson_context,
            )
            updated_exercise.prompt_name = self.current_prompt_name
            updated_exercise.lesson_context = self.lesson_context
            updated_exercise.is_hidden = self.current_hidden_state

            # set deadline and days to complete if use_deadline is True
            alert, deadline, days_to_complete = self.get_deadline_and_days_to_complete()
            # alert the user if no values were provided
            if alert:
                return alert
            updated_exercise.deadline = (
                datetime.fromisoformat(deadline) if deadline else None
            )
            updated_exercise.days_to_complete = days_to_complete

            session.add(updated_exercise)
            session.commit()
            self.load_exercises()
            self.edit_exercise_dialog_is_open = False

        # reset selected tags
        self.selected_tags = []

        return rx.toast.success(
            BT.changes_saved(self.language),
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
                BT.tag_deleted(self.language),
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
        self.current_deadline = ""
        self.current_days_to_complete = ""
        self.use_deadline = True

    def delete_exercise(self, id: int):
        """Delete an exercise from the db."""
        with rx.session() as session:
            exercise = session.exec(select(Exercise).where(Exercise.id == id)).first()
            session.delete(exercise)
            session.commit()
        self.load_exercises()

        return rx.toast.success(
            BT.exercise_deleted(self.language),
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    def load_exercise(self, exercise: Exercise):
        """load the exercise into the state variables."""
        # load the exercise from the state variable so it also contains the tags.
        # Because the argument exercise for some reason does not have the tags loaded.
        for i, e in enumerate(self.exercises):
            if e.id == exercise.id:
                exercise = self.exercises[i]
                break
        self.current_exercise = exercise
        self.current_prompt_name = exercise.prompt_name
        self.lesson_context = exercise.lesson_context
        self.selected_tags = [tag.name for tag in exercise.tags]
        self.lesson_file_name = ""  # reset lesson_file_name
        self.current_hidden_state = exercise.is_hidden
        self.current_deadline = (
            exercise.deadline.strftime("%Y-%m-%dT%H:%M") if exercise.deadline else ""
        )
        self.current_days_to_complete = (
            str(exercise.days_to_complete) if exercise.days_to_complete else ""
        )
        self.use_deadline = (
            exercise.deadline is not None and exercise.days_to_complete is not None
        )

    @rx.event
    def open_add_dialog(self):
        """Open the add/edit dialog."""
        self.reset_exercise_form()
        self.current_prompt_name = self.prompt_names[0] if self.prompt_names else ""
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

    def get_deadline_and_days_to_complete(self):
        """
        set deadline and days to complete if use_deadline is True
        returns a tuple of (alert, deadline, days_to_complete)
        """
        deadline = None
        days_to_complete = None
        if self.use_deadline:
            if self.current_deadline != "" and self.current_days_to_complete != "":
                deadline = self.current_deadline
                days_to_complete = int(self.current_days_to_complete)
            else:
                return (
                    rx.window_alert(
                        "Please enter both a deadline and days to complete."
                    ),
                    None,
                    None,
                )
        return None, deadline, days_to_complete
