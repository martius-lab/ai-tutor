"""
Custom pages for authentication, including login and register pages.
"""

import reflex as rx

from aitutor.pages.navbar import with_navbar

from reflex_local_auth.pages.login import LoginState, login_form
from reflex_local_auth.pages.registration import RegistrationState
from .forms import my_register_form


@with_navbar
def custom_login_page() -> rx.Component:
    """Custom login page."""
    return rx.center(
        rx.cond(
            LoginState.is_hydrated,
            rx.card(login_form()),
        ),
        min_height="85vh",
    )


@with_navbar
def custom_register_page() -> rx.Component:
    """Custom register page."""
    return rx.center(
        rx.cond(
            RegistrationState.is_hydrated,
            rx.card(my_register_form()),
        ),
        min_height="85vh",
    )
