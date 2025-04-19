"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import reflex as rx
from . import (
    pages,
)  # ,components: Uncommented so ruff check is passed. Uncomment when using components.


app = rx.App()
app.add_page(pages.home_default, route="/")
app.add_page(pages.home_default, route="/login")
app.add_page(pages.home_default, route="/register")
app.add_page(pages.chat_default, route="/chat")
app.add_page(pages.add_exercises_default, route="/add-exercises")
app.add_page(
    pages.exercises_default,
    route="/exercises",
    on_load=pages.exercises.ExercisesState.fetch_exercises,
)
