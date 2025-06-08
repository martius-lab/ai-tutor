"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import sys

import reflex as rx
from aitutor import pages
from aitutor.auth.pages import custom_login_page, custom_register_page
from aitutor.config import load_config
from aitutor.pages.manage_excercises import ManageExercisesState
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.chat.state import ChatState
from aitutor.pages.finished_view import FinishedViewState
from aitutor.utilities.create_default_users import create_default_users
import aitutor.routes as routes

# info: add dynamic routes first
app = rx.App()
app.add_page(
    pages.chat_page,
    route=routes.CHAT + "/[exercise_id]",
    on_load=ChatState.load_exercise,
)
app.add_page(
    pages.finished_view_page,
    route=routes.FINISHED_VIEW + "/[exercise_id]",
    on_load=FinishedViewState.load_finished_exercise,
)
app.add_page(pages.home_page, route=routes.HOME)
app.add_page(
    pages.manage_exercises_page,
    route=routes.MANAGE_EXERCISES,
    on_load=ManageExercisesState.initialize,
)
app.add_page(
    pages.exercises_page,
    route=routes.EXERCISES,
    on_load=ExercisesState.fetch_exercises,
)
# reflex_local_auth pages
app.add_page(
    custom_login_page,
    route=routes.LOGIN,
    title="Login",
)
app.add_page(
    custom_register_page,
    route=routes.REGISTER,
    title="Register",
)
app.add_page(pages.not_found_page, route=routes.NOT_FOUND)


async def initialize():
    """Initialization steps that are run once when the app starts."""
    # Note that this function is run as an asynchronous lifespan task, so the
    # application doesn't actually wait for it to be finished before starting to serve
    # requests.  So we should be careful if we ever add any longer-running steps here.

    # load config here, so we fail immediately if there is any issue with it
    try:
        load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    create_default_users()


app.register_lifespan_task(initialize)
