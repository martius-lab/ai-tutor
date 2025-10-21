"""Components for the user settings page."""

import reflex as rx

from aitutor.language_state import LanguageState as LS
from aitutor.pages.login_and_registration.components import password_input
from aitutor.pages.user_settings.state import UserSettingsState


def password_changed_message() -> rx.Component:
    """Render the "password changed" message."""
    return rx.cond(
        UserSettingsState.change_password_message != "",
        rx.callout(
            UserSettingsState.change_password_message,
            icon=rx.cond(
                UserSettingsState.change_password_success, "check", "triangle_alert"
            ),
            color_scheme=rx.cond(
                UserSettingsState.change_password_success, "green", "red"
            ),
            role="alert",
            width="100%",
        ),
    )


def change_password_card() -> rx.Component:
    """Card with form to change the password."""
    return rx.card(
        rx.vstack(
            rx.heading(LS.change_password, size="5"),
            rx.form(
                rx.vstack(
                    password_changed_message(),
                    # -------
                    rx.text(LS.current_password),
                    password_input(
                        "current_password",
                        placeholder=LS.current_password,
                        state=UserSettingsState,
                        required=True,
                    ),
                    rx.text(LS.new_password),
                    password_input(
                        "new_password",
                        placeholder=LS.new_password,
                        state=UserSettingsState,
                        required=True,
                    ),
                    rx.text(LS.confirm_password),
                    password_input(
                        "confirm_new_password",
                        placeholder=LS.confirm_password,
                        state=UserSettingsState,
                        required=True,
                    ),
                    rx.button(
                        LS.save,
                        width="100%",
                        _hover={"cursor": "pointer"},
                    ),
                ),
                on_mount=UserSettingsState.reset_change_password_state,
                on_submit=UserSettingsState.handle_change_password,
                reset_on_submit=True,
            ),
        ),
        # card with is 40em unless the screen is smaller than this, in which case the
        # max_width of 100% applies
        width="40em",
        max_width="100%",
        padding="4",
    )
