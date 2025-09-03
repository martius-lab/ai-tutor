"""This module contains the home page and related components."""

import reflex as rx

from aitutor.pages.navbar import with_navbar
from aitutor.config import get_config
from aitutor.pages.home.state import HomeState


@with_navbar
def home_page() -> rx.Component:
    """Render the homepage with dashboard and info texts."""

    username = HomeState.authenticated_user.username
    config = get_config()

    # TODO: replace dummy data with real data
    # Dummy data
    total_tasks = 10
    completed_tasks = 6
    open_with_deadline = 3
    next_deadline_task = "Mathe Übungsblatt 5 – 10.09.2025"

    progress_value = int((completed_tasks / total_tasks) * 100)

    return rx.center(
        rx.vstack(
            # Dashboard Card
            rx.card(
                rx.vstack(
                    rx.heading(
                        "Dashboard",
                    ),
                    rx.text(f"Willkommen zurück, {username}!", weight="medium"),
                    rx.progress(value=progress_value, max=100, width="100%"),
                    rx.text(f"{completed_tasks}/{total_tasks} Aufgaben erledigt"),
                    rx.text(f"{open_with_deadline} Aufgaben mit Deadline offen"),
                    rx.text(f"Nächste Deadline: {next_deadline_task}"),
                    spacing="4",
                    align="start",
                    width="100%",
                ),
                width="100%",
                padding="4",
            ),
            rx.accordion.root(
                rx.accordion.item(
                    header="How To Use AI-Tutor",
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
            rx.link("about", href="https://github.com/georgmartius/ai-tutor"),
            width="100%",
            align="center",
            justify="center",
        ),
        margin_top="2em",
        margin_bottom="2em",
        width="90%",
    )
