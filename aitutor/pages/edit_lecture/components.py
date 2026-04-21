"""Components for the edit lecture page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.configuration.components import input, text_area
from aitutor.pages.edit_lecture.state import EditLectureState


def lecture_input_field(
    name: str, heading: rx.Var[str], value: str | rx.Var[str]
) -> rx.Component:
    """Render a standard one-line input for the edit lecture form."""
    return input(
        name=name,
        heading=heading,
        value=value,
        on_change=lambda value: EditLectureState.set_lecture_value(name, value),
    )


def lecture_text_area_field(
    name: str,
    heading: rx.Var[str],
    value: str,
) -> rx.Component:
    """Render a standard textarea for the edit lecture form."""
    return text_area(
        name=name,
        heading=heading,
        value=value,
        on_change=lambda value: EditLectureState.set_lecture_value(name, value),
    )


def edit_lecture_form() -> rx.Component:
    """Form for creating or editing lectures."""
    buttons_enabled = EditLectureState.unsaved_changes
    button_hover_style = rx.cond(
        buttons_enabled,
        {"cursor": "pointer"},
        {"cursor": "not-allowed"},
    )

    return rx.card(
        rx.form(
            rx.vstack(
                lecture_input_field(
                    name="lecture_name",
                    heading=LS.lecture_name,
                    value=EditLectureState.lecture_name,
                ),
                lecture_input_field(
                    name="registration_code",
                    heading=LS.registration_code,
                    value=EditLectureState.registration_code,
                ),
                lecture_text_area_field(
                    name="lecture_information_text",
                    heading=LS.lecture_info_text,
                    value=EditLectureState.lecture_information_text,
                ),
                lecture_text_area_field(
                    name="check_conversation_prompt",
                    heading=LS.check_conversation_prompt,
                    value=EditLectureState.check_conversation_prompt,
                ),
                rx.cond(
                    EditLectureState.unsaved_changes,
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
                        on_click=EditLectureState.on_load(),
                        disabled=~buttons_enabled,  # type: ignore
                        _hover=button_hover_style,
                    ),
                    rx.button(
                        rx.cond(
                            EditLectureState.is_new,
                            LS.add,
                            LS.save,
                        ),
                        type="submit",
                        disabled=~buttons_enabled,  # type: ignore
                        _hover=button_hover_style,
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
            ),
            on_submit=EditLectureState.save_lecture,
            width="40em",
            max_width="90vw",
        ),
        outline=rx.cond(
            EditLectureState.unsaved_changes,
            "1px solid orange",
            "none",
        ),
        variant="ghost",
    )
