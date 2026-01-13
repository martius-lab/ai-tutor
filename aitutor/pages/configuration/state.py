"""The state for the configuration page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Config, Exercise, Prompt, UserRole

empty_config: Config = Config(
    id=None,
    check_conversation_prompt="failed to load!",
    response_ai_model="failed to load!",
    check_ai_model="failed to load!",
    how_to_use_text="failed to load!",
    general_information_text="failed to load!",
    lecture_information_text="failed to load!",
    course_name="failed to load!",
    impressum_text="failed to load!",
    registration_code="failed to load!",
)


class ManageConfigState(SessionState):
    """The State for the configuration page."""

    general_unsaved_changes: bool = False
    prompts_unsaved_changes: bool = False
    current_config: Config = empty_config
    prompts: dict[int | None, Prompt] = {}
    replacement_prompt_name: str = ""
    prompt_to_delete: str = ""
    new_prompt_name: str = ""
    new_prompt_template: str = ""
    add_prompt_dialog_open: bool = False

    @rx.event
    def set_general_unsaved_changes(self, unsaved: bool):
        """Sets the unsaved changes flag."""
        self.general_unsaved_changes = unsaved

    @rx.event
    def set_config_value(self, name: str, value: str):
        """Sets a configuration value in the current config."""
        setattr(self.current_config, name, value)
        self.general_unsaved_changes = True

    @rx.event
    def set_prompt_name(self, prompt_id: int | None, name: str):
        """Sets the name of a prompt."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id].name = name
            self.prompts_unsaved_changes = True

    @rx.event
    def set_prompt_template(self, prompt_id: int | None, template: str):
        """Sets the template of a prompt."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id].prompt_template = template
            self.prompts_unsaved_changes = True

    @rx.event
    def set_replacement_prompt_name(self, prompt_name: str):
        """Sets the replacement prompt."""
        self.replacement_prompt_name = prompt_name

    @rx.event
    def set_prompt_to_delete(self, prompt_name: str):
        """Sets the prompt to delete."""
        self.prompt_to_delete = prompt_name

    @rx.event
    def set_new_prompt_name(self, name: str):
        """Sets the name for the new prompt."""
        self.new_prompt_name = name

    @rx.event
    def set_new_prompt(self, prompt: str):
        """Sets the template for the new prompt."""
        self.new_prompt_template = prompt

    @rx.event
    def set_add_prompt_dialog_open(self, is_open: bool):
        """Sets whether the add prompt dialog is open."""
        self.add_prompt_dialog_open = is_open

    @rx.event
    def toggle_default_prompt(self, prompt_id: int | None):
        """Toggle the is_default_prompt flag for a prompt."""
        if prompt_id is None:
            return

        # If this prompt is being set as default, unset all others
        if not self.prompts[prompt_id].is_default_prompt:
            for prompt in self.prompts.values():
                prompt.is_default_prompt = False
            self.prompts[prompt_id].is_default_prompt = True
        else:
            # If unsetting, just unset this one
            self.prompts[prompt_id].is_default_prompt = False

        self.prompts_unsaved_changes = True

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        with rx.session() as session:
            _config = session.get(Config, 1)
            if _config is None:
                raise ValueError("Configuration not found in the database.")
            self.current_config = _config
        self.global_load()
        self.general_unsaved_changes = False
        self.load_prompts_from_db()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.general_unsaved_changes = False
        self.prompts_unsaved_changes = False
        self.current_config = empty_config
        self.prompts = {}
        self.replacement_prompt_name = ""
        self.prompt_to_delete = ""
        self.new_prompt_name = ""
        self.new_prompt_template = ""
        self.add_prompt_dialog_open = False

    @rx.var
    def remaining_prompt_names(self) -> list[str]:
        """Returns the names of the prompts excluding the one to delete."""
        return [
            prompt.name
            for prompt in self.prompts.values()
            if prompt.name != self.prompt_to_delete and prompt.name != ""
        ]

    @rx.var
    def sorted_prompts_list(self) -> list[Prompt]:
        """Returns prompts sorted with default first, then by id."""
        return sorted(
            self.prompts.values(), key=lambda p: (not p.is_default_prompt, p.id or 0)
        )

    @rx.event
    def save_config_to_db(self):
        """Saves the current configuration to the database."""
        with rx.session() as session:
            db_config = session.get(Config, 1)
            if db_config:
                db_config.check_conversation_prompt = (
                    self.current_config.check_conversation_prompt
                )
                db_config.response_ai_model = self.current_config.response_ai_model
                db_config.check_ai_model = self.current_config.check_ai_model
                db_config.how_to_use_text = self.current_config.how_to_use_text
                db_config.general_information_text = (
                    self.current_config.general_information_text
                )
                db_config.lecture_information_text = (
                    self.current_config.lecture_information_text
                )
                db_config.course_name = self.current_config.course_name
                db_config.impressum_text = self.current_config.impressum_text
                db_config.registration_code = self.current_config.registration_code
                session.add(db_config)
                session.commit()

        self.general_unsaved_changes = False

        yield rx.toast.success(
            description=BT.config_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    def names_are_unique(self, names: list[str]) -> bool:
        """Check if all names in the list are unique."""
        return len(names) == len(set(names))

    @rx.event
    def save_prompts_to_db(self):
        """Saves the current prompts to the database."""
        prompts = self.prompts
        if not self.names_are_unique([prompt.name for prompt in prompts.values()]):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if "" in [prompt.name for prompt in prompts.values()]:
            yield rx.toast.error(
                description=BT.prompt_names_nonempty_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        with rx.session() as session:
            session.add_all(prompts.values())
            session.commit()
        self.prompts_unsaved_changes = False
        self.load_prompts_from_db()

        yield rx.toast.success(
            description=BT.prompts_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def delete_prompt(self, prompt_id: int | None):
        """Deletes a prompt from the database."""
        if prompt_id is None:
            return

        with rx.session() as session:
            prompt = session.get(Prompt, prompt_id)
            if prompt:
                # Find the replacement prompt by name
                replacement_prompt = session.exec(
                    select(Prompt).where(Prompt.name == self.replacement_prompt_name)
                ).first()

                if not replacement_prompt:
                    yield rx.toast.error(
                        description=BT.replacement_prompt_not_found(self.language),
                        duration=5000,
                        position="bottom-center",
                        invert=True,
                    )
                    return

                # Update all exercises that use the prompt to be deleted
                exercises = session.exec(
                    select(Exercise).where(Exercise.prompt_id == prompt_id)
                ).all()

                for exercise in exercises:
                    exercise.prompt_id = replacement_prompt.id
                    session.add(exercise)

                # Delete the prompt
                session.delete(prompt)
                session.commit()

        # Remove the prompt from the state
        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            yield rx.toast.success(
                description=BT.prompt_deleted(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
        self.replacement_prompt_name = ""
        self.prompt_to_delete = ""

    @rx.event
    def add_prompt(self):
        """Adds a new prompt to the state"""
        if not self.names_are_unique(
            [prompt.name for prompt in self.prompts.values()] + [self.new_prompt_name]
        ):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        if self.new_prompt_name == "":
            yield rx.toast.error(
                description=BT.prompt_names_nonempty_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            return
        with rx.session() as session:
            new_prompt = Prompt(
                name=self.new_prompt_name,
                prompt_template=self.new_prompt_template,
            )
            session.add(new_prompt)
            session.commit()

            # add the new prompt to the state
            session.refresh(new_prompt)
            if new_prompt.id:
                self.prompts[new_prompt.id] = new_prompt
        self.new_prompt_name = ""
        self.new_prompt_template = ""
        self.add_prompt_dialog_open = False
        yield rx.toast.success(
            description=BT.prompt_added(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def load_prompts_from_db(self):
        """Loads prompts from the database."""
        with rx.session() as session:
            all_prompts = list(session.exec(select(Prompt)).all())
            # Sort prompts: default first, then by id
            sorted_prompts = sorted(
                all_prompts, key=lambda p: (not p.is_default_prompt, p.id or 0)
            )
            self.prompts = {p.id: p for p in sorted_prompts}
        self.prompts_unsaved_changes = False
