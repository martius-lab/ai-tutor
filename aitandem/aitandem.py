"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from .models import Exercise, Tag
from sqlmodel import SQLModel

from . import (
    pages,
)  # ,components: Uncommented so ruff check is passed. Uncomment when using components.


class State(rx.State):
    """The app state."""

    ...

with rx.session() as session: #create a session
    SQLModel.metadata.create_all(session.bind) #create the database

app = rx.App()
app.add_page(pages.home_default, route="/")
app.add_page(pages.settings_default, route="/settings")
app.add_page(pages.login_default, route="/login")
app.add_page(pages.profile_default, route="/profile")
app.add_page(pages.registration_default, route="/register")
app.add_page(pages.exercises_default, route="/exercises")