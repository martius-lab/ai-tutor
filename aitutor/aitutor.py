"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import reflex as rx
from . import (
    pages,
)  # ,components: Uncommented so ruff check is passed. Uncomment when using components.
from .pages.registration import create_admin_user


class State(rx.State):
    """The app state."""

    async def mount(self):
        """Mount admin user method"""
        async for result in create_admin_user():
            yield result


app = rx.App()
app.add_page(pages.home_default, route="/", on_load=State.mount)
app.add_page(pages.settings_default, route="/settings")
app.add_page(pages.login_default, route="/login")
app.add_page(pages.profile_default, route="/profile")
app.add_page(pages.registration_default, route="/register")
app.add_page(pages.chat_default, route="/chat")
app.add_page(pages.add_exercises_default, route="/add-exercises")
app.add_page(
    pages.exercises_default,
    route="/exercises",
    on_load=pages.exercises.ExercisesState.fetch_exercises,
)
