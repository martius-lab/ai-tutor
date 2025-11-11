# ruff: noqa D102
"""State for providing configuration settings."""

import reflex as rx

from aitutor.config import get_config


class ConfigState(rx.State):
    """State for providing configuration settings."""

    # Replicating config values from AiTutorConfig that are used in the frontend (do NOT
    # include anything that is only needed in the backend, especially no sensible data
    # like, for example, the registration code).

    # Using computed vars here, as they do not need to be initialized via some "on_load"
    # event.  This makes it easier to use (we literally need this on every page, so
    # would be annoying to have to inject the on_load everywhere) but might not be
    # optimal in terms of performance?

    # TODO: These variables don't update when the config changes in the database. The
    # user first has to close and reopen the page to see the updated config values.
    # If this is fixed, you also need to change the config_saved success message.

    @rx.var(cache=True, initial_value="")
    def how_to_use_text(self) -> str:
        return get_config().how_to_use_text

    @rx.var(cache=True, initial_value="")
    def general_information_text(self) -> str:
        return get_config().general_information_text

    @rx.var(cache=True, initial_value="")
    def lecture_information_text(self) -> str:
        return get_config().lecture_information_text

    @rx.var(cache=True, initial_value="")
    def course_name(self) -> str:
        return get_config().course_name

    @rx.var(cache=True, initial_value="")
    def impressum_text(self) -> str:
        return get_config().impressum_text
