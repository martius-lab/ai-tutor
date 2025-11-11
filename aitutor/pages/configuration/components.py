"""Components for the configuration page."""

from typing import Optional

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.configuration.state import ConfigurationState


def input(
    *,
    name: str,
    heading: rx.Var[str],
    value: str,
    on_change,
    info: Optional[rx.Component] = None,
) -> rx.Component:
    """Returns an input field with a heading."""
    return rx.vstack(
        rx.cond(
            info is not None,
            rx.hstack(
                rx.text(heading, weight="medium"),
                info,
                spacing="2",
                align="center",
            ),
            rx.text(heading, weight="medium"),
        ),
        rx.input(name=name, value=value, width="100%", on_change=on_change),
        width="40em",
        max_width="100%",
        padding="4",
    )


def text_area(
    *,
    name: str,
    heading: rx.Var[str],
    value: str,
    on_change,
    info: Optional[rx.Component] = None,
) -> rx.Component:
    """Returns a text area with a heading."""
    return rx.vstack(
        rx.cond(
            info is not None,
            rx.hstack(
                rx.text(heading, weight="medium"),
                info,
                spacing="2",
                align="center",
            ),
            rx.text(heading, weight="medium"),
        ),
        rx.text_area(
            name=name,
            value=value,
            width="100%",
            resize="vertical",
            rows="4",
            on_change=on_change,
        ),
        width="40em",
        max_width="100%",
        padding="4",
    )


def info_icon(info_text: str | rx.Var[str]) -> rx.Component:
    """Returns an info icon popover"""
    return rx.popover.root(
        rx.popover.trigger(
            rx.icon("info", size=20),
            _hover={"cursor": "pointer"},
        ),
        rx.popover.content(
            rx.markdown(info_text),
            padding="4",
            max_width="300px",
        ),
    )


def config_form() -> rx.Component:
    """Returns input fields for configuration settings."""
    return rx.card(
        rx.form(
            rx.vstack(
                input(
                    name="course_name",
                    heading=LS.course_name,
                    value=ConfigurationState.current_config.course_name,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "course_name", value
                    ),
                ),
                input(
                    name="registration_code",
                    heading=LS.registration_code,
                    value=ConfigurationState.current_config.registration_code,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "registration_code", value
                    ),
                    info=info_icon(LS.registration_code_info),
                ),
                input(
                    name="response_ai_model",
                    heading=LS.response_ai_model,
                    value=ConfigurationState.current_config.response_ai_model,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "response_ai_model", value
                    ),
                    info=info_icon(LS.response_ai_model_info),
                ),
                input(
                    name="check_ai_model",
                    heading=LS.check_ai_model,
                    value=ConfigurationState.current_config.check_ai_model,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "check_ai_model", value
                    ),
                    info=info_icon(LS.check_ai_model_info),
                ),
                text_area(
                    name="check_conversation_prompt",
                    heading=LS.check_conversation_prompt,
                    value=ConfigurationState.current_config.check_conversation_prompt,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "check_conversation_prompt", value
                    ),
                    info=info_icon(LS.check_conversation_prompt_info),
                ),
                text_area(
                    name="how_to_use_text",
                    heading=LS.how_to_use_text,
                    value=ConfigurationState.current_config.how_to_use_text,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "how_to_use_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="general_info_text",
                    heading=LS.general_info_text,
                    value=ConfigurationState.current_config.general_information_text,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "general_information_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="lecture_info_text",
                    heading=LS.lecture_info_text,
                    value=ConfigurationState.current_config.lecture_information_text,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "lecture_information_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="impressum",
                    heading=LS.impressum,
                    value=ConfigurationState.current_config.impressum_text,
                    on_change=lambda value: ConfigurationState.set_config_value(
                        "impressum_text", value
                    ),
                    info=info_icon(LS.impressum_info),
                ),
                rx.cond(
                    ConfigurationState.unsaved_changes,
                    rx.callout(
                        LS.unsaved_changes_info,
                        icon="info",
                        width="100%",
                        color_scheme="orange",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        LS.cancel,
                        color_scheme="red",
                        type="button",
                        on_click=ConfigurationState.on_load(),
                        disabled=~ConfigurationState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ConfigurationState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    rx.button(
                        LS.save,
                        type="submit",
                        disabled=~ConfigurationState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ConfigurationState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
            on_submit=ConfigurationState.save_config_to_db(),
            width="40em",
            max_width="90vw",
        ),
        outline=rx.cond(
            ConfigurationState.unsaved_changes,
            "1px solid orange",
            "none",
        ),
        variant="ghost",
    )
