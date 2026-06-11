"""Components for password reset account email pages."""

from typing import Literal

import reflex as rx
from reflex_local_auth.pages.components import MIN_WIDTH

from aitutor import routes
from aitutor.language_state import LanguageState
from aitutor.pages.account_emails.state import ForgotPasswordState, ResetPasswordState
from aitutor.pages.login_and_registration.components import input, password_input


def account_callout(
    message, color_scheme: Literal["green", "red"], icon: str
) -> rx.Component:
    """Render an account flow status message."""
    return rx.callout(
        message,
        icon=icon,
        color_scheme=color_scheme,
        role="alert",
        width="100%",
    )


def forgot_password_form() -> rx.Component:
    """Render the password reset request form."""
    return rx.form(
        rx.vstack(
            rx.input(
                type="hidden",
                name="language",
                value=LanguageState.language,
            ),
            rx.heading(LanguageState.reset_password, size="7"),
            rx.cond(
                ForgotPasswordState.error_message != "",
                account_callout(
                    ForgotPasswordState.error_message,
                    color_scheme="red",
                    icon="triangle_alert",
                ),
            ),
            rx.cond(
                ForgotPasswordState.message != "",
                account_callout(
                    ForgotPasswordState.message,
                    color_scheme="green",
                    icon="check",
                ),
            ),
            rx.text(LanguageState.username_or_email),
            input(
                "identifier",
                placeholder=LanguageState.username_or_email,
                required=True,
            ),
            rx.button(
                LanguageState.send_reset_link,
                width="100%",
                _hover={"cursor": "pointer"},
            ),
            rx.center(rx.link(LanguageState.log_in, href=routes.LOGIN), width="100%"),
            min_width=MIN_WIDTH,
        ),
        on_submit=ForgotPasswordState.request_password_reset,
    )


def reset_password_form() -> rx.Component:
    """Render the form for setting a new password."""
    return rx.form(
        rx.vstack(
            rx.input(
                type="hidden",
                name="language",
                value=LanguageState.language,
            ),
            rx.heading(LanguageState.set_new_password, size="7"),
            rx.cond(
                ResetPasswordState.error_message != "",
                account_callout(
                    ResetPasswordState.error_message,
                    color_scheme="red",
                    icon="triangle_alert",
                ),
            ),
            rx.cond(
                ResetPasswordState.message != "",
                account_callout(
                    ResetPasswordState.message,
                    color_scheme="green",
                    icon="check",
                ),
            ),
            rx.text(LanguageState.new_password),
            password_input(
                "new_password",
                placeholder=LanguageState.new_password,
                required=True,
            ),
            rx.text(LanguageState.confirm_new_password),
            password_input(
                "confirm_password",
                placeholder=LanguageState.confirm_new_password,
                required=True,
            ),
            rx.button(
                LanguageState.change_password,
                width="100%",
                _hover={"cursor": "pointer"},
            ),
            min_width=MIN_WIDTH,
        ),
        on_submit=ResetPasswordState.reset_password,
    )
