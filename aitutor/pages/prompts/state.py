"""The state for the prompts page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Exercise, Prompt, UserRole


class ManagePromptsState(SessionState):
    """The State for the configuration page."""

    unsaved_changes: bool = False
    prompts: dict[int | None, Prompt] = {}
    replacement_prompt_name: str = ""
    prompt_to_delete: str = ""
    new_prompt_name: str = ""
    new_prompt_template: str = ""
    add_prompt_dialog_open: bool = False

    @rx.event
    def set_prompt_name(self, prompt_id: int | None, name: str):
        """Sets the name of a prompt."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id].name = name
            self.unsaved_changes = True

    @rx.event
    def set_prompt_template(self, prompt_id: int | None, template: str):
        """Sets the template of a prompt."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id].prompt_template = template
            self.unsaved_changes = True

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
    @state_require_role_at_least(UserRole.TUTOR)
    def on_load(self):
        """Initialization for the page."""
        self.global_load()
        self.load_prompts_from_db()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.unsaved_changes = False
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
        self.unsaved_changes = False
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
            prompts = session.exec(select(Prompt).order_by(Prompt.id))  # type: ignore
            self.prompts = {p.id: p for p in prompts}
        self.unsaved_changes = False
