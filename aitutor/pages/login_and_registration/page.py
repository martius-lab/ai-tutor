"""The login and the registration page."""

import reflex as rx

from aitutor.pages.navbar import with_navbar

from reflex_local_auth.pages.login import LoginState
from reflex_local_auth.pages.registration import RegistrationState
from aitutor.pages.login_and_registration.components import (
    login_form,
    register_form,
)

# login --------------------------------------------------------------------------------


@with_navbar("")
def custom_login_page() -> rx.Component:
    """Custom login page."""
    return rx.center(
        rx.cond(
            LoginState.is_hydrated,
            rx.card(login_form()),
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )


# registration -------------------------------------------------------------------------


@with_navbar("")
def custom_register_page() -> rx.Component:
    """Custom register page."""
    return rx.center(
        rx.cond(
            RegistrationState.is_hydrated,
            rx.card(register_form()),
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
