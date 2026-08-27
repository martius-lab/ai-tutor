"""Components for the configuration page."""

from typing import Optional

import reflex as rx

from aitutor.components.dialogs import destructive_confirm
from aitutor.language_state import LanguageState as LS
from aitutor.models import BannerMessageType, LecturerRegistrationToken
from aitutor.pages.configuration.state import (
    CONFIG_FIELD_MAX_LENGTHS,
    LecturerRegistrationTokenState,
    ManageConfigState,
)

CARD_WIDTH = "42em"
CARD_MAX_WIDTH = "90vw"


def input(
    *,
    name: str,
    heading: rx.Var[str],
    value: str | rx.Var[str],
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


def banner_form_group() -> rx.Component:
    """Returns a form group card wrapping banner-related controls."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(LS.banner_section_title, weight="bold", as_="h3"),
                info_icon(LS.banner_section_info),
                align="center",
                spacing="2",
            ),
            rx.hstack(
                rx.text(LS.banner_is_open_label, weight="medium"),
                rx.checkbox(
                    checked=ManageConfigState.current_config.banner_is_open,
                    on_change=ManageConfigState.set_banner_is_open,
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.cond(
                ManageConfigState.current_config.banner_is_open,
                rx.fragment(
                    text_area(
                        name="banner_message",
                        heading=LS.banner_message,
                        value=ManageConfigState.current_config.banner_message,
                        on_change=lambda value: ManageConfigState.set_config_value(
                            "banner_message", value
                        ),
                        color_scheme=rx.cond(
                            ManageConfigState.is_banner_message_invalid, "red", "gray"
                        ),
                    ),
                    rx.cond(
                        ManageConfigState.is_banner_message_invalid,
                        rx.text(
                            LS.banner_message_required_error,
                            color_scheme="red",
                            size="2",
                        ),
                    ),
                    rx.hstack(
                        rx.text(LS.banner_message_type, weight="medium"),
                        rx.select(
                            [e.value for e in BannerMessageType],
                            value=ManageConfigState.current_config.banner_message_type,
                            on_change=ManageConfigState.set_banner_message_type,
                        ),
                        width="100%",
                        align="center",
                        justify="between",
                    ),
                ),
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="4",
        variant="surface",
    )


def config_form() -> rx.Component:
    """Returns input fields for configuration settings."""
    return rx.card(
        rx.heading(LS.general_settings, as_="h2"),
        rx.spacer(height="1em"),
        rx.form(
            rx.vstack(
                input(
                    name="registration_code",
                    heading=LS.registration_code,
                    value=ManageConfigState.current_config.registration_code,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "registration_code", value
                    ),
                    info=info_icon(LS.registration_code_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["registration_code"],
                ),
                input(
                    name="response_ai_model",
                    heading=LS.response_ai_model,
                    value=ManageConfigState.current_config.response_ai_model,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "response_ai_model", value
                    ),
                    info=info_icon(LS.response_ai_model_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["response_ai_model"],
                ),
                input(
                    name="check_ai_model",
                    heading=LS.check_ai_model,
                    value=ManageConfigState.current_config.check_ai_model,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "check_ai_model", value
                    ),
                    info=info_icon(LS.check_ai_model_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["check_ai_model"],
                ),
                input(
                    name="exercise_token_limit",
                    heading=LS.exercise_token_limit,
                    value=ManageConfigState.exercise_token_limit_str,
                    on_change=ManageConfigState.set_exercise_token_limit,
                    type="number",
                    min="1",
                    info=info_icon(LS.exercise_token_limit_info),
                ),
                text_area(
                    name="how_to_use_text",
                    heading=LS.how_to_use_text,
                    value=ManageConfigState.current_config.how_to_use_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "how_to_use_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["how_to_use_text"],
                ),
                text_area(
                    name="general_info_text",
                    heading=LS.general_info_text,
                    value=ManageConfigState.current_config.general_information_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "general_information_text", value
                    ),
                    info=info_icon(LS.info_texts_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["general_information_text"],
                ),
                text_area(
                    name="impressum",
                    heading=LS.impressum,
                    value=ManageConfigState.current_config.impressum_text,
                    on_change=lambda value: ManageConfigState.set_config_value(
                        "impressum_text", value
                    ),
                    info=info_icon(LS.impressum_info),
                    max_length=CONFIG_FIELD_MAX_LENGTHS["impressum_text"],
                ),
                banner_form_group(),
                rx.cond(
                    ManageConfigState.unsaved_changes,
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
                        disabled=~ManageConfigState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ManageConfigState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    rx.button(
                        LS.save,
                        type="submit",
                        disabled=~ManageConfigState.unsaved_changes,  # type: ignore
                        _hover=rx.cond(
                            ManageConfigState.unsaved_changes,
                            {"cursor": "pointer"},
                            {"cursor": "not-allowed"},
                        ),
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
            ),
            on_submit=ManageConfigState.save_config_to_db,
        ),
        width=CARD_WIDTH,
        max_width=CARD_MAX_WIDTH,
        outline=rx.cond(
            ManageConfigState.unsaved_changes,
            "1px solid orange",
            "none",
        ),
    )


def btn_delete_lecturer_registration_token(
    token: LecturerRegistrationToken,
) -> rx.Component:
    """Button to delete a lecturer registration token with confirmation dialog."""

    return destructive_confirm(
        title=LS.delete,
        description=LS.delete_token_description,
        confirm_text=LS.delete,
        cancel_text=LS.cancel,
        on_confirm=LecturerRegistrationTokenState.delete_token(token.id),  # type: ignore
        trigger=rx.icon_button(
            "trash",
            title=LS.delete,
            color_scheme="red",
            variant="outline",
            size="1",
        ),
    )


def btn_add_lecturer_registration_token() -> rx.Component:
    """Dialog to add a new lecturer registration token."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.hstack(rx.icon("plus", size=16), LS.add),
                _hover={"cursor": "pointer"},
                variant="outline",
                size="1",
            )
        ),
        rx.dialog.content(
            rx.dialog.title(LS.lecturer_registration_token_dialog_title),
            rx.dialog.description(LS.expires_at),
            rx.form(
                rx.flex(
                    rx.input(
                        name="expires_at",
                        type="date",
                        default_value=LecturerRegistrationTokenState.default_expires_at,
                    ),
                    rx.flex(
                        rx.dialog.close(rx.button(LS.cancel, variant="outline")),
                        rx.form.submit(rx.button(LS.add, type="submit"), as_child=True),
                        spacing="3",
                        justify="end",
                    ),
                    spacing="4",
                    direction="column",
                ),
                on_submit=LecturerRegistrationTokenState.generate_new_token,
            ),
        ),
        open=LecturerRegistrationTokenState.add_dialog_is_open,
        on_open_change=LecturerRegistrationTokenState.set_add_dialog_is_open,
    )


def lecturer_registration_token_table_row(
    token: LecturerRegistrationToken,
) -> rx.Component:
    """A row for the lecturer registration token table."""
    is_expired = token.is_expired
    return rx.table.row(
        rx.table.cell(token.token),
        rx.table.cell(
            rx.hstack(
                rx.moment(token.expires_at, format="YYYY-MM-DD HH:mm"),
                rx.cond(is_expired, rx.badge(LS.expired, color_scheme="red")),
                spacing="2",
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    ~is_expired,
                    rx.icon_button(
                        "clipboard_copy",
                        title=LS.copy_link,
                        variant="outline",
                        size="1",
                        on_click=rx.set_clipboard(
                            LecturerRegistrationTokenState.link_base + token.token
                        ),
                    ),
                ),
                btn_delete_lecturer_registration_token(token),
                spacing="1",
            ),
            align="right",
        ),
        color=rx.cond(is_expired, rx.color("gray", 8), None),
    )


def lecturer_registraton_token_table() -> rx.Component:
    """Table of existing lecturer registration tokens."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(LS.token),
                rx.table.column_header_cell(LS.expires_at),
                rx.table.column_header_cell(btn_add_lecturer_registration_token()),
            ),
        ),
        rx.table.body(
            rx.foreach(
                LecturerRegistrationTokenState.tokens,
                lecturer_registration_token_table_row,
            ),
        ),
    )


def lecturer_registration_token_management() -> rx.Component:
    """Returns a component for managing lecturer registration tokens."""
    return rx.card(
        rx.heading(LS.lecturer_registration_token_management, as_="h2"),
        rx.spacer(height="1em"),
        rx.text(LS.lecturer_registration_token_management_info),
        lecturer_registraton_token_table(),
        spacing="2",
        padding="4",
        width=CARD_WIDTH,
        max_width=CARD_MAX_WIDTH,
    )
