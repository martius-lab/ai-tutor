"""The state for the configuration page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.config import get_config_db_model
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Config, Prompt, UserRole

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

    unsaved_changes: bool = False
    current_config: Config = empty_config
    prompts: list[Prompt] = []
    manage_prompt_dialog_open: bool = False
    replacement_prompt_name: str = ""
    prompt_to_delete: int = -1

    @rx.event
    def set_unsaved_changes(self, unsaved: bool):
        """Sets the unsaved changes flag."""
        self.unsaved_changes = unsaved

    @rx.event
    def set_config_value(self, name: str, value: str):
        """Sets a configuration value in the current config."""
        setattr(self.current_config, name, value)
        self.unsaved_changes = True

    @rx.event
    def set_prompt_name(self, prompt_id: int, name: str):
        """Sets the name of a prompt."""
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                prompt.name = name
                break

    @rx.event
    def set_prompt_template(self, prompt_id: int, template: str):
        """Sets the template of a prompt."""
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                prompt.prompt_template = template
                break

    @rx.event
    def set_manage_prompt_dialog_open(self, is_open: bool):
        """Sets the manage prompt dialog open state."""
        self.manage_prompt_dialog_open = is_open

    @rx.event
    def set_replacement_prompt_name(self, prompt_name: str):
        """Sets the replacement prompt."""
        self.replacement_prompt_name = prompt_name

    @rx.event
    def set_prompt_to_delete(self, prompt_id: int):
        """Sets the prompt to delete."""
        self.prompt_to_delete = prompt_id

    @rx.event
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        self.global_load()
        self.current_config = get_config_db_model()
        self.unsaved_changes = False
        self.load_prompts_from_db()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.unsaved_changes = False
        self.current_config = empty_config
        self.prompts = []
        self.manage_prompt_dialog_open = False
        self.replacement_prompt_name = ""
        self.prompt_to_delete = -1

    @rx.var
    def remaining_prompt_names(self) -> list[str]:
        """Returns the names of the prompts excluding the one to delete."""
        return [
            prompt.name for prompt in self.prompts if prompt.id != self.prompt_to_delete
        ]

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

        self.unsaved_changes = False

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
        if not self.names_are_unique([prompt.name for prompt in prompts]):
            yield rx.toast.error(
                description=BT.prompt_names_unique_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            self.load_prompts_from_db()
            return
        with rx.session() as session:
            for prompt in prompts:
                # create a new instance, detached from old session
                new_prompt = Prompt(
                    id=prompt.id,
                    name=prompt.name,
                    prompt_template=prompt.prompt_template,
                )
                session.merge(new_prompt)  # insert/update ORM object
            session.commit()
        self.set_manage_prompt_dialog_open(False)
        yield rx.toast.success(
            description=BT.prompts_saved(self.language),
            duration=5000,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    def delete_prompt(self, prompt_id: int):
        """Deletes a prompt from the database."""
        with rx.session() as session:
            prompt = session.get(Prompt, prompt_id)
            if prompt:
                session.delete(prompt)
                session.commit()
        self.load_prompts_from_db()
        self.replacement_prompt_name = ""
        self.prompt_to_delete = -1
        # TODO: replace deleted prompt with replacement prompt in the exercises

    def load_prompts_from_db(self):
        """Loads prompts from the database."""
        with rx.session() as session:
            prompts = session.exec(select(Prompt).order_by(Prompt.id))  # type: ignore
            self.prompts = list(prompts)
