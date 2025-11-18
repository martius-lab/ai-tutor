# ruff: noqa D102
"""State for providing configuration settings."""

import reflex as rx

from aitutor.config import get_config


class DisplayConfigState(rx.State):
    """
    Provides configuration strings used in the frontend.
    """

    # !!Do NOT include sensible data here that is only used in the backend
    # (e.g., the registration code).!!

    # Using computed vars here, as they do not need to be initialized via some "on_load"
    # event.  This makes it easier to use (we literally need this on every page, so
    # would be annoying to have to inject the on_load everywhere) but might not be
    # optimal in terms of performance?

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
