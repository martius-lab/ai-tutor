"""Components for managing lecture-specific prompts."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.models import Prompt
from aitutor.pages.configuration.components import input, text_area
from aitutor.pages.lecture_prompts.state import LectureManagePromptsState


def prompt_card(prompt: Prompt) -> rx.Component:
    """A card representing a global or lecture-specific prompt."""
    is_global = prompt.lecture_id == None  # noqa: E711
    is_default = prompt.id == LectureManagePromptsState.current_default_prompt_id
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.cond(
                    is_global,
                    rx.badge("Global", color_scheme="blue", variant="soft"),
                    rx.box(),
                ),
                input(
                    name="prompt_name",
                    heading=LS.prompt_name,
                    value=prompt.name,
                    on_change=lambda value: LectureManagePromptsState.set_prompt_name(
                        prompt.id, value
                    ),
                    placeholder=LS.prompt_name_placeholder,
                    disabled=is_global,
                ),
                text_area(
                    name="prompt_template",
                    heading=LS.prompt,
                    value=prompt.prompt_template,
                    on_change=lambda value: LectureManagePromptsState.set_prompt_template(
                        prompt.id, value
                    ),
                    placeholder=LS.prompt_variables_info,
                    disabled=is_global,
                ),
                rx.hover_card.root(
                    rx.hover_card.trigger(
                        rx.button(
                            rx.icon(
                                "star",
                                size=18,
                                fill=rx.cond(
                                    is_default,
                                    "currentColor",
                                    "none",
                                ),
                            ),
                            rx.cond(
                                is_default,
                                LS.default_prompt,
                                LS.mark_as_default_prompt,
                            ),
                            on_click=lambda: LectureManagePromptsState.set_default_prompt(
                                prompt.id
                            ),
                            variant="soft",
                            color_scheme=rx.cond(
                                is_default,
                                "green",
                                "gray",
                            ),
                            _hover={"cursor": "pointer", "opacity": "0.8"},
                            width="100%",
                            max_width="300px",
                        ),
                    ),
                    rx.hover_card.content(rx.text(LS.default_prompt_hover)),
                ),
                width="90%",
            ),
            rx.cond(
                is_global,
                rx.box(width="10%"),
                delete_prompt_dialog(prompt),
            ),
            align="center",
            spacing="4",
        ),
        padding="4",
        width="100%",
    )


def delete_prompt_dialog(prompt: Prompt) -> rx.Component:
    """Delete button with confirmation dialog for lecture prompts."""
    return rx.box(
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.icon_button(
                    rx.icon("trash"),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    _hover={"cursor": "pointer"},
                    on_click=LectureManagePromptsState.set_prompt_to_delete(prompt.name),
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title(LS.delete_prompt),
                rx.alert_dialog.description(LS.delete_prompt_description),
                rx.box(height="0.5em"),
                rx.text(LS.replacement_prompt + ":", weight="medium"),
                rx.box(height="0.5em"),
                rx.select(
                    LectureManagePromptsState.remaining_prompt_names,
                    value=LectureManagePromptsState.replacement_prompt_name,
                    on_change=LectureManagePromptsState.set_replacement_prompt_name,
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            rx.text(LS.cancel),
                            _hover={"cursor": "pointer"},
                            on_click=[
                                LectureManagePromptsState.set_replacement_prompt_name(""),
                                LectureManagePromptsState.set_prompt_to_delete(""),
                            ],
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            LS.delete,
                            color_scheme="red",
                            on_click=LectureManagePromptsState.delete_prompt(prompt.id),
                            _hover=rx.cond(
                                LectureManagePromptsState.replacement_prompt_name == "",
                                {"cursor": "not-allowed"},
                                {"cursor": "pointer"},
                            ),
                            disabled=LectureManagePromptsState.replacement_prompt_name
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
    )


def add_prompt_dialog() -> rx.Component:
    """Dialog to add a new lecture-specific prompt."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("plus"),
                LS.add_prompt,
                _hover={"cursor": "pointer"},
                on_click=LectureManagePromptsState.set_add_prompt_dialog_open(True),
            ),
        ),
        rx.dialog.content(
            rx.vstack(
                input(
                    name="prompt_name",
                    heading=LS.prompt_name,
                    value=LectureManagePromptsState.new_prompt_name,
                    on_change=LectureManagePromptsState.set_new_prompt_name,
                    placeholder=LS.prompt_name_placeholder,
                ),
                text_area(
                    name="prompt_template",
                    heading=LS.prompt,
                    value=LectureManagePromptsState.new_prompt_template,
                    on_change=LectureManagePromptsState.set_new_prompt,
                    placeholder=LS.prompt_variables_info,
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            rx.text(LS.cancel),
                            _hover={"cursor": "pointer"},
                            variant="outline",
                            on_click=LectureManagePromptsState.set_add_prompt_dialog_open(
                                False
                            ),
                        ),
                    ),
                    rx.button(
                        LS.add_prompt,
                        color_scheme="green",
                        _hover={"cursor": "pointer"},
                        on_click=LectureManagePromptsState.add_prompt,
                    ),
                    justify="end",
                    width="100%",
                    margin_top="1em",
                ),
            ),
            width="40em",
            max_width="90vw",
        ),
        open=LectureManagePromptsState.add_prompt_dialog_open,
    )


def lecture_prompt_management() -> rx.Component:
    """Prompt management card for one lecture."""
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
                LectureManagePromptsState.prompts.values(),
                prompt_card,
            ),
            rx.cond(
                LectureManagePromptsState.unsaved_changes,
                rx.callout(
                    LS.unsaved_changes_info,
                    icon="info",
                    width="100%",
                    color_scheme="orange",
                ),
            ),
            rx.box(height="1em"),
            rx.hstack(
                rx.button(
                    LS.discard_changes,
                    _hover=rx.cond(
                        LectureManagePromptsState.unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    color_scheme="red",
                    on_click=LectureManagePromptsState.load_prompts_from_db,
                    disabled=~LectureManagePromptsState.unsaved_changes,  # type: ignore
                ),
                rx.button(
                    LS.save,
                    _hover=rx.cond(
                        LectureManagePromptsState.unsaved_changes,
                        {"cursor": "pointer"},
                        {"cursor": "not-allowed"},
                    ),
                    on_click=LectureManagePromptsState.save_prompts_to_db,
                    disabled=~LectureManagePromptsState.unsaved_changes,  # type: ignore
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
            LectureManagePromptsState.unsaved_changes,
            "1px solid orange",
            "none",
        ),
    )