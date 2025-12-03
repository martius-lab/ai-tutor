"""Components for the configuration page."""

from typing import Optional

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.models import Prompt
from aitutor.pages.configuration.state import ManageConfigState
from aitutor.states.config_state import DisplayConfigState


def input(
    *,
    name: str,
    heading: rx.Var[str],
    value: str,
    on_change,
    info: Optional[rx.Component] = None,
    **props,
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
        rx.input(name=name, value=value, width="100%", on_change=on_change, **props),
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
    **props,
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
            **props,
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
                    value=ManageConfigState.current_config.course_name,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "course_name", value
                    ),
                ),
                input(
                    name="registration_code",
                    heading=LS.registration_code,
                    value=ManageConfigState.current_config.registration_code,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "registration_code", value
                    ),
                    info=info_icon(LS.registration_code_info),
                ),
                input(
                    name="response_ai_model",
                    heading=LS.response_ai_model,
                    value=ManageConfigState.current_config.response_ai_model,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "response_ai_model", value
                    ),
                    info=info_icon(LS.response_ai_model_info),
                ),
                input(
                    name="check_ai_model",
                    heading=LS.check_ai_model,
                    value=ManageConfigState.current_config.check_ai_model,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "check_ai_model", value
                    ),
                    info=info_icon(LS.check_ai_model_info),
                ),
                text_area(
                    name="check_conversation_prompt",
                    heading=LS.check_conversation_prompt,
                    value=ManageConfigState.current_config.check_conversation_prompt,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "check_conversation_prompt", value
                    ),
                    info=info_icon(LS.check_conversation_prompt_info),
                ),
                text_area(
                    name="how_to_use_text",
                    heading=LS.how_to_use_text,
                    value=ManageConfigState.current_config.how_to_use_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "how_to_use_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="general_info_text",
                    heading=LS.general_info_text,
                    value=ManageConfigState.current_config.general_information_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "general_information_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="lecture_info_text",
                    heading=LS.lecture_info_text,
                    value=ManageConfigState.current_config.lecture_information_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "lecture_information_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                ),
                text_area(
                    name="impressum",
                    heading=LS.impressum,
                    value=ManageConfigState.current_config.impressum_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "impressum_text", value
                    ),
                    info=info_icon(LS.impressum_info),
                ),
                rx.cond(
                    ManageConfigState.general_unsaved_changes,
                    rx.callout(
                        LS.unsaved_changes_info,
                        icon="info",
                        width="100%",
                        color_scheme="orange",
                    ),
                ),
                rx.hstack(
                    rx.button(
                        LS.discard_changes,
                        color_scheme="red",
                        type="button",
                        on_click=ManageConfigState.on_load(),
                        disabled=~ManageConfigState.general_unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ManageConfigState.general_unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    rx.button(
                        LS.save,
                        type="submit",
                        disabled=~ManageConfigState.general_unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ManageConfigState.general_unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
            on_submit=[
                ManageConfigState.save_config_to_db(),
                DisplayConfigState.refresh_config_strings(),
            ],
            width="40em",
            max_width="90vw",
        ),
        outline=rx.cond(
            ManageConfigState.general_unsaved_changes,
            "1px solid orange",
            "none",
        ),
        variant="ghost",
    )


def prompt_management() -> rx.Component:
    """The Button to manage prompts."""
    return rx.card(
        rx.vstack(
            rx.callout(
                rx.hstack(
                    rx.icon("info"),
                    rx.markdown(
                        LS.prompt_variables_info,
                        margin_top="0",
                        margin_bottom="0",
                        align="left",
                    ),
                    align="center",
                ),
                color_scheme="blue",
                role="alert",
                width="100%",
            ),
            rx.foreach(
                ManageConfigState.prompts.values(),
                prompt_card,
            ),
            rx.button(
                rx.icon("plus"),
                LS.add_prompt,
                _hover={"cursor": "pointer"},
                on_click=ManageConfigState.add_prompt,
            ),
            rx.cond(
                ManageConfigState.prompts_unsaved_changes,
                rx.callout(
                    LS.unsaved_changes_info,
                    icon="info",
                    width="100%",
                    color_scheme="orange",
                ),
            ),
            rx.box(
                height="1em",
            ),
            rx.hstack(
                rx.button(
                    LS.discard_changes,
                    _hover=rx.cond(
                        ManageConfigState.prompts_unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    color_scheme="red",
                    on_click=ManageConfigState.load_prompts_from_db,
                    disabled=~ManageConfigState.prompts_unsaved_changes,  # type: ignore
                ),
                rx.button(
                    LS.save,
                    _hover=rx.cond(
                        ManageConfigState.prompts_unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    color_scheme="green",
                    on_click=ManageConfigState.save_prompts_to_db,
                    disabled=~ManageConfigState.prompts_unsaved_changes,  # type: ignore
                ),
                width="100%",
                justify="end",
            ),
            spacing="4",
            align="center",
        ),
        width="40em",
        max_width="90vw",
        variant="ghost",
        outline=rx.cond(
            ManageConfigState.prompts_unsaved_changes,
            "1px solid orange",
            "none",
        ),
    )


def prompt_card(prompt: Prompt) -> rx.Component:
    """A card representing a prompt."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                input(
                    name="prompt_name",
                    heading=LS.prompt_name,
                    value=prompt.name,
                    on_change=lambda value: ManageConfigState.set_prompt_name(
                        prompt.id, value
                    ),
                    placeholder=LS.prompt_name_placeholder,
                ),
                text_area(
                    name="prompt_template",
                    heading=LS.prompt,
                    value=prompt.prompt_template,
                    on_change=lambda value: ManageConfigState.set_prompt_template(
                        prompt.id, value
                    ),
                    placeholder=LS.prompt_variables_info,
                ),
                width="90%",
            ),
            # delete button with confirmation dialog
            rx.box(
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.icon_button(
                            rx.icon("trash"),
                            size="2",
                            variant="ghost",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                            on_click=ManageConfigState.set_prompt_to_delete(
                                prompt.name
                            ),
                        ),
                    ),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title(LS.delete_prompt),
                        rx.alert_dialog.description(LS.delete_prompt_description),
                        rx.box(
                            height="0.5em",
                        ),
                        rx.text(LS.replacement_prompt + ":", weight="medium"),
                        rx.box(
                            height="0.5em",
                        ),
                        rx.select(
                            ManageConfigState.remaining_prompt_names,
                            value=ManageConfigState.replacement_prompt_name,
                            on_change=ManageConfigState.set_replacement_prompt_name,
                        ),
                        rx.hstack(
                            rx.alert_dialog.cancel(
                                rx.button(
                                    rx.text(LS.cancel),
                                    _hover={"cursor": "pointer"},
                                    on_click=[
                                        ManageConfigState.set_replacement_prompt_name(
                                            ""
                                        ),
                                        ManageConfigState.set_prompt_to_delete(""),
                                    ],
                                ),
                            ),
                            rx.alert_dialog.action(
                                rx.button(
                                    LS.delete,
                                    color_scheme="red",
                                    on_click=ManageConfigState.delete_prompt(prompt.id),
                                    _hover=rx.cond(
                                        ManageConfigState.replacement_prompt_name == "",
                                        {"cursor": "not-allowed"},
                                        {"cursor": "pointer"},
                                    ),
                                    disabled=ManageConfigState.replacement_prompt_name
                                    == "",
                                ),
                            ),
                            justify="end",
                            width="100%",
                            margin_top="1em",
                        ),
                    ),
                ),
                width="10%",
            ),
            align="center",
            spacing="4",
        ),
        padding="4",
        width="100%",
    )
