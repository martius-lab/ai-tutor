"""The Components for the home page."""

import reflex as rx

from aitutor.pages.home.state import HomeState
from aitutor.routes import LOGIN, REGISTER
from aitutor.config import get_config


def dashboard_card():
    """Render the dashboard card"""
    username = HomeState.authenticated_user.username
    exercises_num = HomeState.exercises_with_result.length()  # type: ignore

    return (
        rx.card(
            rx.cond(
                HomeState.is_authenticated,
                # dashboard for logged in users
                rx.vstack(
                    rx.heading(
                        "Dashboard",
                    ),
                    rx.text(f"Welcome back, {username}!", weight="medium"),
                    rx.progress(value=HomeState.progress_value, max=100, width="100%"),  # type: ignore
                    rx.hstack(
                        rx.icon("circle-check", color="green", size=20),
                        rx.cond(
                            exercises_num > 0,
                            rx.text(
                                f"{HomeState.completed_exercises_num} \
                                /{exercises_num} open exercises submitted"
                            ),
                            rx.text("No pending exercises"),
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.text("Next Deadline:", weight="bold"),
                        rx.text(HomeState.next_deadline_task),
                        align="center",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                # dashboard for not logged in users
                rx.vstack(
                    rx.heading("Dashboard"),
                    rx.text(
                        "Welcome to the AI Tutor. Please log in or register to "
                        "see your progress.",
                        weight="medium",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon(
                                    "log-in",
                                    size=15,
                                ),
                                rx.text(
                                    "Log in",
                                    size="2",
                                    margin_bottom="6px",
                                    margin_top="6px",
                                ),
                                align="center",
                                justify="center",
                                spacing="1",
                            ),
                            _hover={"cursor": "pointer"},
                            color_scheme="iris",
                            on_click=rx.redirect(LOGIN),
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(
                                    "notepad-text",
                                    size=15,
                                ),
                                rx.text(
                                    "Register",
                                    size="2",
                                    margin_bottom="6px",
                                    margin_top="6px",
                                ),
                                align="center",
                                justify="center",
                                spacing="1",
                            ),
                            _hover={"cursor": "pointer"},
                            color_scheme="green",
                            on_click=rx.redirect(REGISTER),
                        ),
                    ),
                    align="start",
                    width="100%",
                ),
            ),
            width="100%",
            padding="4",
        ),
    )


def info_accordion():
    """Render the info accordion"""
    config = get_config()
    return (
        rx.accordion.root(
            rx.accordion.item(
                header="How To Use AI Tutor",
                content=rx.markdown(config.how_to_use_text),
            ),
            rx.accordion.item(
                header="General Information",
                content=rx.markdown(config.general_information_text),
            ),
            rx.accordion.item(
                header="Lecture Information",
                content=rx.markdown(config.lecture_information_text),
            ),
            width="100%",
            collapsible=True,
            variant="outline",
        ),
    )
