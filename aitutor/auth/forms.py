"""
The forms and components for user authentication,
including registration and error handling.
"""

import reflex as rx
import reflex_local_auth
from reflex_local_auth.pages.components import MIN_WIDTH
import aitutor.routes as routes

from aitutor.auth.state import MyRegisterState
from aitutor.language_state import LanguageState


def login_error() -> rx.Component:
    """Render the login error message."""
    return rx.cond(
        reflex_local_auth.LoginState.error_message != "",
        rx.callout(
            reflex_local_auth.LoginState.error_message,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
        ),
    )


def input(name, placeholder, **props) -> rx.Component:
    """Render a 100% width input with a placeholder."""
    return rx.input(
        placeholder=placeholder,
        id=name,
        name=name,
        width="100%",
        **props,
    )


def my_login_form() -> rx.Component:
    """Render the login form."""
    return rx.form(
        rx.vstack(
            rx.heading(LanguageState.login_heading, size="7"),
            login_error(),
            rx.text(LanguageState.username),
            input(
                "username",
                placeholder=LanguageState.username,
                required=True,
            ),
            rx.text(LanguageState.password),
            input(
                "password",
                placeholder=LanguageState.password,
                type="password",
                required=True,
            ),
            rx.button(LanguageState.log_in, width="100%", _hover={"cursor": "pointer"}),
            rx.center(
                rx.link(LanguageState.register, on_click=rx.redirect(routes.REGISTER)),
                width="100%",
            ),
            min_width=MIN_WIDTH,
        ),
        on_submit=reflex_local_auth.LoginState.on_submit,
    )


def register_error() -> rx.Component:
    """Render the registration error message."""
    return rx.cond(
        MyRegisterState.error_message != "",
        rx.callout(
            MyRegisterState.error_message,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
        ),
    )


def success_message() -> rx.Component:
    """Render the successful registration message."""
    return rx.cond(
        MyRegisterState.success,
        rx.callout(
            LanguageState.successful_registration,
            icon="check",
            color_scheme="green",
            role="alert",
            width="100%",
        ),
    )


def my_register_form() -> rx.Component:
    """Render the registration form."""
    return rx.form(
        rx.vstack(
            rx.heading(LanguageState.register_heading, size="7"),
            register_error(),
            success_message(),
            rx.text(LanguageState.username),
            input(
                "username",
                placeholder=LanguageState.username,
                required=True,
                value=MyRegisterState.username,
                on_change=MyRegisterState.set_username,
            ),
            rx.text(LanguageState.email),
            input(
                "email",
                placeholder=LanguageState.email,
                type="email",
                required=True,
                value=MyRegisterState.email,
                on_change=MyRegisterState.set_email,
            ),
            rx.text(LanguageState.password),
            input(
                "password",
                placeholder=LanguageState.password,
                type="password",
                required=True,
                value=MyRegisterState.password,
                on_change=MyRegisterState.set_password,
            ),
            rx.text(LanguageState.confirm_password),
            input(
                "confirm_password",
                placeholder=LanguageState.confirm_password,
                type="password",
                required=True,
                value=MyRegisterState.confirm_password,
                on_change=MyRegisterState.set_confirm_password,
            ),
            rx.button(
                LanguageState.register,
                width="100%",
                _hover={"cursor": "pointer"},
            ),
            rx.center(
                rx.link(
                    LanguageState.log_in,
                    on_click=lambda: rx.redirect(routes.LOGIN),
                ),
                width="100%",
            ),
            min_width=MIN_WIDTH,
        ),
        on_submit=MyRegisterState.handle_custom_registration,
    )
