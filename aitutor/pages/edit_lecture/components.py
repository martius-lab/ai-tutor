"""Components for the edit lecture page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.configuration.components import input, text_area
from aitutor.pages.edit_lecture.state import EditLectureState


def edit_lecture_form() -> rx.Component:
    """Form for creating or editing lectures."""
    return rx.card(
        rx.form(
            rx.vstack(
                input(
                    name="lecture_name",
                    heading=LS.lecture_name,
                    value=EditLectureState.lecture_name,
                    on_change=lambda value: EditLectureState.set_lecture_value(
                        "lecture_name", value
                    ),
                ),
                input(
                    name="registration_code",
                    heading=LS.registration_code,
                    value=EditLectureState.registration_code,
                    on_change=lambda value: EditLectureState.set_lecture_value(
                        "registration_code", value
                    ),
                ),
                text_area(
                    name="lecture_information_text",
                    heading=LS.lecture_info_text,
                    value=EditLectureState.lecture_information_text,
                    on_change=lambda value: EditLectureState.set_lecture_value(
                        "lecture_information_text", value
                    ),
                ),
                text_area(
                    name="check_conversation_prompt",
                    heading=LS.check_conversation_prompt,
                    value=EditLectureState.check_conversation_prompt,
                    on_change=lambda value: EditLectureState.set_lecture_value(
                        "check_conversation_prompt", value
                    ),
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
                        disabled=~EditLectureState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            EditLectureState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            EditLectureState.is_new,
                            LS.add,
                            LS.save,
                        ),
                        type="submit",
                        disabled=~EditLectureState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            EditLectureState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
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
