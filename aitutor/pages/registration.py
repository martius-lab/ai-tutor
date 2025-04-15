"""New user registration form and validation logic."""

from __future__ import annotations

import os
import re
import asyncio

import reflex as rx
from dotenv import load_dotenv
from collections.abc import AsyncGenerator

from ..base_state import State
from ..models import User
from .sidebar import with_sidebar


class RegistrationState(State):
    """Handle registration form submission
    and redirect to login page after registration."""

    success: bool = False  # Boolean to check if registration was a success

    async def handle_registration(
        self, form_data
    ) -> AsyncGenerator[rx.event.EventSpec | list[rx.event.EventSpec] | None, None]:
        """Handle registration form on_submit.

        Set error_message appropriately based on validation results.

        Args:
            form_data: A dict of form fields and values.
        """
        with rx.session() as session:
            email = form_data["email"]
            special_char_pattern = r"[!@#$%^&*(),.?\":{}|<> \s]"
            valid_email_pattern = r"^.+@.+\..+$"

            if not email:
                yield rx.toast.error(
                    "E-Mail cannot be empty.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("email")
                return

            if not re.match(valid_email_pattern, email):
                yield rx.toast.error(
                    "Please enter a valid e-mail address.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("email")
                return

            existing_user = session.exec(
                User.select().where(User.email == email)
            ).one_or_none()

            if existing_user is not None:
                yield rx.toast.error(
                    f"{email} is already registered. Try a different E-Mail",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield [rx.set_value("email", ""), rx.set_focus("email")]
                return

            password = form_data["password"]

            if not password:
                yield rx.toast.error(
                    "Password cannot be empty.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("password")
                return

            if len(password) < 8:
                yield rx.toast.error(
                    "Password too short. Password must be at least 8 characters.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("password")
                return

            if not re.search(special_char_pattern, password):
                yield rx.toast.error(
                    "Password must contain at least one these "
                    'special characters: [!@#$%^&*(),.?":{}|<>] '
                    "a blank space also works.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("password")
                return

            if password != form_data["confirm_password"]:
                yield rx.toast.error(
                    "Passwords do not match.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                # reset pw and set focus
                yield [
                    rx.set_value("confirm_password", ""),
                    rx.set_focus("confirm_password"),
                ]
                return

            if not form_data["checkbox"]:
                yield rx.toast.error(
                    "You have to agree to the Terms and Conditions.",
                    duration=3500,
                    position="bottom-center",
                    invert=True,
                )
                yield rx.set_focus("checkbox")
                return

            # Create the new user and add it to the database.
            new_user = User()  # type: ignore
            new_user.email = email
            new_user.password_hash = User.hash_password(password)
            new_user.enabled = True
            session.add(new_user)
            session.commit()

        # Set success and redirect to login page after a brief delay.
        self.success = True
        yield rx.set_value("email", "")
        await asyncio.sleep(2)
        yield [rx.redirect("/login"), RegistrationState.set_success(False)]


async def create_admin_user():
    """Creates admin user if it does not exist."""
    # error message / load .env variables
    if not load_dotenv():
        yield rx.window_alert(
            "Admin was not created because admin credentials were not set correctly"
            " in the .env file. Please read the manual."
        )
        return

    # set hard-coded admin credentials
    admin_email = os.getenv("ADMIN_EMAIL", "admin")
    admin_pw = os.getenv("ADMIN_PW", "admin")

    with rx.session() as session:
        # check if admin already exists
        existing_admin = session.exec(
            User.select().where(User.email == admin_email)
        ).one_or_none()

        # if admin does not exist
        if not existing_admin:
            # create admin
            admin = User()
            admin.email = admin_email
            admin.password_hash = User.hash_password(admin_pw)
            admin.enabled = True
            admin.role = "teacher"

            # write to db
            session.add(admin)
            session.commit()


@rx.page(route="/register")
@with_sidebar
def registration_default() -> rx.Component:
    """Render the registration page.

    Returns:
        A reflex component.
    """
    register_form = rx.form(
        rx.center(
            rx.color_mode.button(position="top-right", type="button"),
            rx.card(
                rx.vstack(
                    rx.center(
                        rx.heading(
                            "Create an account",
                            size="6",
                            as_="h2",
                            text_align="center",
                            width="100%",
                        ),
                        direction="column",
                        spacing="5",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "E-Mail address",
                            size="3",
                            weight="medium",
                            text_align="left",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("user")),
                            placeholder="AI-Tandempartner@example.com",
                            size="3",
                            width="100%",
                            id="email",
                        ),
                        justify="start",
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Password",
                            size="3",
                            weight="medium",
                            text_align="left",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("lock")),
                            placeholder="Enter your password",
                            size="3",
                            width="100%",
                            id="password",
                            type="password",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("lock")),
                            placeholder="Confirm password",
                            size="3",
                            width="100%",
                            id="confirm_password",
                            type="password",
                        ),
                        justify="start",
                        spacing="2",
                        width="100%",
                    ),
                    rx.box(
                        rx.checkbox(
                            "Agree to Terms and Conditions",
                            default_checked=False,
                            spacing="2",
                            id="checkbox",
                        ),
                        width="100%",
                    ),
                    rx.button("Register", type="submit", size="3", width="100%"),
                    rx.center(
                        rx.text("Already registered?", size="3"),
                        rx.link("Sign in", href="/login", size="3"),
                        opacity="0.8",
                        spacing="2",
                        direction="row",
                        width="100%",
                    ),
                    spacing="6",
                    width="100%",
                ),
                max_width="28em",
                size="4",
                width="100%",
            ),
            height="85vh",
        ),
        on_submit=RegistrationState.handle_registration,
    )
    return rx.fragment(
        rx.cond(
            RegistrationState.success,
            rx.center(
                rx.vstack(
                    rx.heading("Registration Successful!"),
                    rx.text(
                        "Your registration was successful,"
                        " you will be redirected to the login page now."
                    ),
                    rx.spinner(size="3"),
                    align="center",
                ),
                height="100vh",
            ),
        ),
        register_form,
    )
