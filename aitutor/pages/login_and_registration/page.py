"""The login and the registration page."""

import reflex as rx
from reflex_local_auth.pages.login import LoginState
from reflex_local_auth.pages.registration import RegistrationState

from aitutor.pages.login_and_registration.components import (
    login_form,
    register_form,
)
from aitutor.pages.navbar import with_navbar

# login --------------------------------------------------------------------------------


@with_navbar()
def custom_login_page() -> rx.Component:
    """Custom login page."""
    return rx.center(
        rx.cond(
            LoginState.is_hydrated,
            rx.card(login_form()),
        ),
        class_name="page-frame",
    )


# registration -------------------------------------------------------------------------


@with_navbar()
def custom_register_page() -> rx.Component:
    """Custom register page."""
    return rx.center(
        rx.cond(
            RegistrationState.is_hydrated,
            rx.card(register_form()),
        ),
        class_name="page-frame",
    )
