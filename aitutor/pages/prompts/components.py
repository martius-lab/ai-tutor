"""Components for managing prompts."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.models import Prompt
from aitutor.pages.configuration.components import input, text_area
from aitutor.pages.prompts.state import ManagePromptsState


def prompt_card(prompt: Prompt) -> rx.Component:
    """A card representing a prompt."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                input(
                    name="prompt_name",
                    heading=LS.prompt_name,
                    value=prompt.name,
                    on_change=lambda value: ManagePromptsState.set_prompt_name(
                        prompt.id, value
                    ),
                    placeholder=LS.prompt_name_placeholder,
                ),
                text_area(
                    name="prompt_template",
                    heading=LS.prompt,
                    value=prompt.prompt_template,
                    on_change=lambda value: ManagePromptsState.set_prompt_template(
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
                            on_click=ManagePromptsState.set_prompt_to_delete(
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
                            ManagePromptsState.remaining_prompt_names,
                            value=ManagePromptsState.replacement_prompt_name,
                            on_change=ManagePromptsState.set_replacement_prompt_name,
                        ),
                        rx.hstack(
                            rx.alert_dialog.cancel(
                                rx.button(
                                    rx.text(LS.cancel),
                                    _hover={"cursor": "pointer"},
                                    on_click=[
                                        ManagePromptsState.set_replacement_prompt_name(
                                            ""
                                        ),
                                        ManagePromptsState.set_prompt_to_delete(""),
                                    ],
                                ),
                            ),
                            rx.alert_dialog.action(
                                rx.button(
                                    LS.delete,
                                    color_scheme="red",
                                    on_click=ManagePromptsState.delete_prompt(
                                        prompt.id
                                    ),
                                    _hover=rx.cond(
                                        ManagePromptsState.replacement_prompt_name
                                        == "",
                                        {"cursor": "not-allowed"},
                                        {"cursor": "pointer"},
                                    ),
                                    disabled=ManagePromptsState.replacement_prompt_name
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


def add_prompt_dialog() -> rx.Component:
    """The Dialog to add a new prompt."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("plus"),
                LS.add_prompt,
                _hover={"cursor": "pointer"},
                on_click=ManagePromptsState.set_add_prompt_dialog_open(True),
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                input(
                    name="prompt_name",
                    heading=LS.prompt_name,
                    value=ManagePromptsState.new_prompt_name,
                    on_change=ManagePromptsState.set_new_prompt_name,
                    placeholder=LS.prompt_name_placeholder,
                ),
                text_area(
                    name="prompt_template",
                    heading=LS.prompt,
                    value=ManagePromptsState.new_prompt_template,
                    on_change=ManagePromptsState.set_new_prompt,
                    placeholder=LS.prompt_variables_info,
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            rx.text(LS.cancel),
                            _hover={"cursor": "pointer"},
                            variant="outline",
                            on_click=ManagePromptsState.set_add_prompt_dialog_open(
                                False
                            ),
                        ),
                    ),
                    rx.button(
                        LS.add_prompt,
                        color_scheme="green",
                        _hover={"cursor": "pointer"},
                        on_click=ManagePromptsState.add_prompt,
                    ),
                    justify="end",
                    width="100%",
                    margin_top="1em",
                ),
            ),
            width="40em",
            max_width="90vw",
        ),
        open=ManagePromptsState.add_prompt_dialog_open,
    )


def prompt_management() -> rx.Component:
    """The Button to manage prompts."""
    return rx.card(
        rx.vstack(
            add_prompt_dialog(),
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
                role="alert",
                width="100%",
            ),
            rx.foreach(
                ManagePromptsState.prompts.values(),
                prompt_card,
            ),
            rx.cond(
                ManagePromptsState.unsaved_changes,
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
                        ManagePromptsState.unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    color_scheme="red",
                    on_click=ManagePromptsState.load_prompts_from_db,
                    disabled=~ManagePromptsState.unsaved_changes,  # type: ignore
                ),
                rx.button(
                    LS.save,
                    _hover=rx.cond(
                        ManagePromptsState.unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    on_click=ManagePromptsState.save_prompts_to_db,
                    disabled=~ManagePromptsState.unsaved_changes,  # type: ignore
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
            ManagePromptsState.unsaved_changes,
            "1px solid orange",
            "none",
        ),
    )
