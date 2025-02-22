"""New user registration form and validation logic."""

from __future__ import annotations

import os
import reflex as rx
import re
import asyncio

from dotenv import load_dotenv
from collections.abc import AsyncGenerator
from sqlalchemy import select
from ..base_state import State
from ..models import User


class RegistrationState(State):
    """Handle registration form submission
    and redirect to login page after registration."""

    success: bool = False  # Boolean to check if registration was a success
    error_message: str = ""  # Empty string for error messages

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
            valid_email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            special_char_pattern = r"[!@#$%^&*(),.?\":{}|<>]"
            if not email:
                self.error_message = "E-Mail cannot be empty"
                yield rx.set_focus("email")
                return
            if not re.match(valid_email_pattern, email):
                self.error_message = "Please enter a valid E-Mail address"
                yield rx.set_focus("email")
                return
            existing_user = session.exec(
                select(User).where(User.email == email)
            ).one_or_none()
            if existing_user is not None:
                self.error_message = (
                    f"{email} is already registered. Try a different E-Mail"
                )
                yield [rx.set_value("email", ""), rx.set_focus("email")]
                return
            password = form_data["password"]
            if not password:
                self.error_message = "Password cannot be empty"
                yield rx.set_focus("password")
                return
            if len(password) < 8:
                self.error_message = (
                    "Password too short. Password must be at least 8 characters"
                )
                yield rx.set_focus("password")
                return
            if not re.search(special_char_pattern, password):
                self.error_message = (
                    "Password must contain at least one these "
                    'special characters: [!@#$%^&*(),.?":{}|<>]'
                )
                yield rx.set_focus("password")
                return
            if password != form_data["confirm_password"]:
                self.error_message = "Passwords do not match"
                yield [
                    rx.set_value("confirm_password", ""),
                    rx.set_focus("confirm_password"),
                ]
                return
            if not form_data["checkbox"]:
                self.error_message = "You have to agree to the Terms and Conditions"
                yield rx.set_focus("checkbox")
                return
            # Create the new user and add it to the database.
            new_user = User()  # type: ignore
            new_user.email = email
            new_user.password_hash = User.hash_password(password)
            new_user.enabled = True
            session.add(new_user)
            session.commit()
        # Set success and redirect to home page after a brief delay.
        self.error_message = ""
        self.success = True
        yield rx.set_value("email", "")
        await asyncio.sleep(2)
        yield [rx.redirect("/"), RegistrationState.set_success(False)]


async def create_admin_user():
    """Creates admin user if it does not exist."""
    # error message for non existing admin credentials
    if not load_dotenv():
        yield rx.window_alert("Admin was not created because admin credentials were not set correctly in the .env file. Please read the manual. ")
        return
    # load .env data
    load_dotenv()
    # set hardcoded admin credentials
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pw = os.getenv("ADMIN_PW")

    with rx.session() as session:
        # check if admin already exists
        existing_admin = session.exec(
            select(User).where(User.email == admin_email)  # type:ignore
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
                        rx.link("Sign in", href="#", size="3"),
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
                        " you will be redirected home now."
                    ),
                    rx.spinner(size="3"),
                    align="center",
                ),
                height="100vh",
            ),
        ),
        register_form,
        rx.cond(  # conditionally show error messages
            RegistrationState.error_message != "",
            rx.text(
                RegistrationState.error_message,
                align="center",
            ),
        ),
    )
