"""Components for the login and for the registration page."""

import reflex as rx
import reflex_local_auth
from reflex_local_auth.pages.components import MIN_WIDTH

import aitutor.routes as routes
from aitutor.pages.login_and_registration.state import (
    ShowPasswordMixin,
    MyLoginState,
    MyRegisterState,
)
from aitutor.language_state import LanguageState
from aitutor.pages.legal_infos.loader_functions import get_privacy_notice_short


def input(name, placeholder, **props) -> rx.Component:
    """Render a 100% width input with a placeholder."""
    return rx.input(
        placeholder=placeholder,
        id=name,
        name=name,
        width="100%",
        **props,
    )


def password_input(
    name, placeholder, state: type[ShowPasswordMixin], **props
) -> rx.Component:
    """
    Render a 100% width password input with a placeholder. It also has
    a toggle button to show the password.
    """
    return rx.hstack(
        rx.input(
            placeholder=placeholder,
            id=name,
            name=name,
            type=rx.cond(state.password_visible, "text", "password"),
            width="100%",
            **props,
        ),
        rx.cond(
            state.password_visible,
            rx.icon(
                "eye",
                on_click=state.toggle_password_visibility,
                _hover={"cursor": "pointer"},
            ),
            rx.icon(
                "eye-off",
                on_click=state.toggle_password_visibility,
                _hover={"cursor": "pointer"},
            ),
        ),
        align="center",
        width="100%",
    )


# login --------------------------------------------------------------------------------


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


def login_form() -> rx.Component:
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
            password_input(
                "password",
                placeholder=LanguageState.password,
                state=MyLoginState,
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


# register -----------------------------------------------------------------------------


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


def register_success() -> rx.Component:
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


def register_form() -> rx.Component:
    """Render the registration form."""
    privacy_notice = get_privacy_notice_short()
    return rx.form(
        rx.vstack(
            rx.heading(LanguageState.register_heading, size="7"),
            register_error(),
            register_success(),
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
            password_input(
                "password",
                placeholder=LanguageState.password,
                state=MyRegisterState,
                required=True,
                value=MyRegisterState.password,
                on_change=MyRegisterState.set_password,
            ),
            rx.text(LanguageState.confirm_password),
            password_input(
                "confirm_password",
                placeholder=LanguageState.confirm_password,
                state=MyRegisterState,
                required=True,
                value=MyRegisterState.confirm_password,
                on_change=MyRegisterState.set_confirm_password,
            ),
            rx.text(LanguageState.registration_code),
            input(
                "registration_code",
                placeholder=LanguageState.registration_code_placeholder,
                required=True,
                value=MyRegisterState.registration_code,
                on_change=MyRegisterState.set_registration_code,
            ),
            rx.cond(
                privacy_notice,
                rx.callout(
                    rx.hstack(
                        rx.icon("info"),
                        rx.markdown(
                            privacy_notice,
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
