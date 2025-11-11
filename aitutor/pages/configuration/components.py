"""Components for the configuration page."""

import reflex as rx
from aitutor.language_state import LanguageState as LS
from aitutor.pages.configuration.state import ConfigurationState


def input(
    *, name: str, heading: rx.Var[str], placeholder: str | rx.Var[str], value: str
) -> rx.Component:
    """Returns an input field with a heading."""
    return rx.vstack(
        rx.text(heading, weight="medium"),
        rx.input(placeholder=placeholder, name=name, value=value, width="100%"),
        width="40em",
        max_width="100%",
        padding="4",
    )


def text_area(
    *, name: str, heading: rx.Var[str], placeholder: str | rx.Var[str], value: str
) -> rx.Component:
    """Returns a text area with a heading."""
    return rx.vstack(
        rx.text(heading, weight="medium"),
        rx.text_area(placeholder=placeholder, name=name, value=value, width="100%"),
        width="40em",
        max_width="100%",
        padding="4",
    )


def config_form() -> rx.Component:
    """Returns input fields for configuration settings."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "Config settings",
                _hover={"cursor": "pointer"},
                on_click=ConfigurationState.set_config_dialog_open(True),
            ),
        ),
        rx.dialog.content(
            rx.form(
                rx.vstack(
                    input(
                        name="course_name",
                        heading=LS.course_name,
                        placeholder=LS.course_name_placeholder,
                        value="",
                    ),
                    input(
                        name="registration_code",
                        heading=LS.registration_code,
                        placeholder=LS.registration_code_placeholder_config,
                        value="",
                    ),
                    input(
                        name="response_ai_model",
                        heading=LS.response_ai_model,
                        placeholder="e.g. gpt-4.1-mini",
                        value="",
                    ),
                    input(
                        name="check_ai_model",
                        heading=LS.check_ai_model,
                        placeholder="e.g. gpt-4.1",
                        value="",
                    ),
                    text_area(
                        name="check_conversation_prompt",
                        heading=LS.check_conversation_prompt,
                        placeholder=LS.check_conversation_prompt_placeholder,
                        value="",
                    ),
                    text_area(
                        name="how_to_use_text",
                        heading=LS.how_to_use_text,
                        placeholder=LS.info_text_placeholder,
                        value="",
                    ),
                    text_area(
                        name="general_info_text",
                        heading=LS.general_info_text,
                        placeholder=LS.info_text_placeholder,
                        value="",
                    ),
                    text_area(
                        name="lecture_info_text",
                        heading=LS.lecture_info_text,
                        placeholder=LS.info_text_placeholder,
                        value="",
                    ),
                    text_area(
                        name="impressum",
                        heading=LS.impressum,
                        placeholder=LS.impressum_placeholder,
                        value="",
                    ),
                    rx.hstack(
                        rx.button(
                            LS.cancel,
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                            on_click=ConfigurationState.set_config_dialog_open(False),
                        ),
                        rx.button(
                            LS.save,
                            _hover={"cursor": "pointer"},
                        ),
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                )
            )
        ),
        open=ConfigurationState.config_dialog_open,
    )
