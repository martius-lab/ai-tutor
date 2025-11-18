# ruff: noqa D102
"""State for providing configuration settings."""

import reflex as rx

from aitutor.config import get_config


class DisplayConfigState(rx.State):
    """
    This state provides configuration strings used in the frontend as rx.vars.
    !!Do NOT include sensible data here that is only used in the backend
    (e.g., the registration code).!!
    """

    # This variable is used to trigger recomputation of the config string vars.
    # rx.vars are only recomputed when a contained state variable changes. So we add
    # a state var to the rx.vars so we can manually trigger recomputation.
    trigger_var: bool = False

    @rx.var(cache=True, initial_value="")
    def how_to_use_text(self) -> str:
        self.trigger_var
        return get_config().how_to_use_text

    @rx.var(cache=True, initial_value="")
    def general_information_text(self) -> str:
        self.trigger_var
        return get_config().general_information_text

    @rx.var(cache=True, initial_value="")
    def lecture_information_text(self) -> str:
        self.trigger_var
        return get_config().lecture_information_text

    @rx.var(cache=True, initial_value="")
    def course_name(self) -> str:
        self.trigger_var
        return get_config().course_name

    @rx.var(cache=True, initial_value="")
    def impressum_text(self) -> str:
        self.trigger_var
        return get_config().impressum_text

    @rx.event
    def refresh_config_strings(self):
        """Refresh the config strings by toggling the trigger_var."""
        self.trigger_var = not self.trigger_var
