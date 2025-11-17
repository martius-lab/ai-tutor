"""The Components for the home page."""

import reflex as rx

from aitutor import ConfigStringsState, routes
from aitutor.language_state import LanguageState
from aitutor.pages.home.state import HomeState
from aitutor.routes import LOGIN, REGISTER


def dashboard_card():
    """Render the dashboard card"""
    exercises_num = HomeState.exercises_with_result.length()  # type: ignore

    return (
        rx.card(
            rx.cond(
                HomeState.is_authenticated,
                # dashboard for logged in users
                rx.vstack(
                    rx.heading(
                        LanguageState.dashboard,
                    ),
                    rx.text(LanguageState.welcome_back, weight="medium"),
                    rx.progress(value=HomeState.progress_value, max=100, width="100%"),  # type: ignore
                    rx.hstack(
                        rx.icon("circle-check", color="green", size=20),
                        rx.cond(
                            exercises_num > 0,
                            rx.text(
                                f"{HomeState.completed_exercises_num} \
                                /{exercises_num} \
                                    {LanguageState.open_exercises_submitted}"
                            ),
                            rx.text(LanguageState.no_pending_exercises),
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.text(LanguageState.next_deadline, weight="bold"),
                        rx.cond(
                            HomeState.next_deadline_task,
                            rx.text(HomeState.next_deadline_task),
                            rx.text(LanguageState.no_upcoming_deadlines),
                        ),
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                # dashboard for not logged in users
                rx.vstack(
                    rx.heading(LanguageState.dashboard),
                    rx.text(
                        LanguageState.welcome_message,
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
                                    LanguageState.log_in,
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
                                    LanguageState.register,
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
    return (
        rx.cond(
            (ConfigStringsState.how_to_use_text != "")
            | (ConfigStringsState.general_information_text != "")
            | (ConfigStringsState.lecture_information_text != ""),
            rx.accordion.root(
                rx.cond(
                    ConfigStringsState.how_to_use_text != "",
                    rx.accordion.item(
                        header=LanguageState.how_to_use_aitutor,
                        content=rx.markdown(ConfigStringsState.how_to_use_text),
                    ),
                ),
                rx.cond(
                    ConfigStringsState.general_information_text != "",
                    rx.accordion.item(
                        header=LanguageState.general_info,
                        content=rx.markdown(
                            ConfigStringsState.general_information_text
                        ),
                    ),
                ),
                rx.cond(
                    ConfigStringsState.lecture_information_text != "",
                    rx.accordion.item(
                        header=LanguageState.lecture_info,
                        content=rx.markdown(
                            ConfigStringsState.lecture_information_text
                        ),
                    ),
                ),
                width="100%",
                collapsible=True,
                variant="outline",
            ),
        ),
    )


def legal_info_links():
    """Render the links for Impressum and privacy notice"""
    return rx.hstack(
        rx.link(
            LanguageState.impressum,
            href=routes.IMPRESSUM,
        ),
        rx.link(
            LanguageState.privacy_notice,
            href=routes.PRIVACY_NOTICE,
        ),
    )
