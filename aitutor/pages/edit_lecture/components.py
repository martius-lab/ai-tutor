"""Components for the edit lecture page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.components import password_input
from aitutor.language_state import LanguageState as LS
from aitutor.pages.configuration.components import input, text_area
from aitutor.pages.edit_lecture.state import EditLectureState


def back_to_my_lectures_button() -> rx.Component:
    """Render the button for navigating back to my lectures."""
    return rx.button(
        rx.icon("arrow-left", size=20),
        LS.my_lectures,
        on_click=rx.redirect(routes.MY_LECTURES),
        _hover={"cursor": "pointer"},
    )


def edit_lecture_header() -> rx.Component:
    """Render the edit lecture page header."""
    return rx.hstack(
        back_to_my_lectures_button(),
        align="center",
        width="40em",
        max_width="90vw",
    )


def lecture_input_field(
    name: str,
    heading: rx.Var[str],
    value: str | rx.Var[str],
    required: bool = False,
) -> rx.Component:
    """Render a standard one-line input for the edit lecture form."""
    return input(
        name=name,
        heading=heading,
        value=value,
        on_change=lambda value: EditLectureState.set_lecture_value(name, value),
        required=required,
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


def copy_join_link_button() -> rx.Component:
    """Render a button that copies the direct lecture join link."""
    return rx.cond(
        ~EditLectureState.is_new,
        rx.button(
            rx.icon("copy", size=16),
            LS.copy_join_link,
            type="button",
            variant="outline",
            on_click=[
                rx.call_script(
                    "navigator.clipboard.writeText("
                    f"window.location.origin + '{routes.ALL_LECTURES}/' + "
                    f"{EditLectureState.current_lecture_id}"
                    ")"
                ),
                rx.toast.success(
                    description=LS.join_link_copied,
                    duration=4000,
                    position="bottom-center",
                    invert=True,
                ),
            ],
            _hover={"cursor": "pointer"},
        ),
    )


def delete_lecture_dialog() -> rx.Component:
    """Render the password-confirmed delete lecture dialog."""
    delete_password_is_empty = EditLectureState.delete_confirmation_password == ""
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.button(
                rx.icon("trash-2", size=16),
                LS.delete_lecture,
                type="button",
                color_scheme="red",
                variant="outline",
                disabled=EditLectureState.is_new,
                _hover=rx.cond(
                    EditLectureState.is_new,
                    {"cursor": "not-allowed"},
                    {"cursor": "pointer"},
                ),
            ),
        ),
        rx.alert_dialog.content(
            rx.vstack(
                rx.alert_dialog.title(LS.delete_lecture),
                rx.alert_dialog.description(LS.delete_lecture_description),
                password_input(
                    id="delete_lecture_confirmation_password",
                    placeholder=LS.password_to_confirm_deletion,
                    value=EditLectureState.delete_confirmation_password,
                    on_change=EditLectureState.set_delete_confirmation_password,
                    width="100%",
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            LS.cancel,
                            type="button",
                            variant="outline",
                            on_click=EditLectureState.clear_delete_confirmation_password,
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            LS.delete_lecture,
                            type="button",
                            color_scheme="red",
                            on_click=EditLectureState.delete_current_lecture,
                            disabled=delete_password_is_empty,
                            _hover=rx.cond(
                                delete_password_is_empty,
                                {"cursor": "not-allowed"},
                                {"cursor": "pointer"},
                            ),
                        ),
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                align="start",
                width="100%",
            )
        ),
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
                    required=True,
                ),
                lecture_input_field(
                    name="lecturer_name",
                    heading=LS.lecture_lecturer,
                    value=EditLectureState.lecturer_name,
                    required=True,
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
                    copy_join_link_button(),
                    rx.cond(
                        ~EditLectureState.is_new,
                        delete_lecture_dialog(),
                    ),
                    rx.spacer(),
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


def edit_lecture_content() -> rx.Component:
    """Main content for the edit lecture page."""
    return rx.vstack(
        edit_lecture_header(),
        edit_lecture_form(),
        spacing="3",
        align="center",
        width="100%",
    )
