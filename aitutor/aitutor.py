"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import reflex as rx
from aitutor import pages
from aitutor.auth.pages import custom_login_page, custom_register_page
from aitutor.config import load_config
from aitutor.pages.add_excercises import AddExerciseState
from aitutor.pages.exercises import ExercisesState
from aitutor.pages.chat import ChatState
from aitutor.utilities.create_default_users import create_default_users
import aitutor.routes as routes

# info: add dynamic routes first
app = rx.App()
app.add_page(
    pages.chat_default,
    route=routes.CHAT + "/[exercise_id]",
    on_load=ChatState.load_exercise,
)
app.add_page(pages.home_default, route=routes.HOME)
app.add_page(
    pages.add_exercises_default,
    route=routes.ADD_EXERCISE,
    on_load=AddExerciseState.initialize,
)
app.add_page(
    pages.exercises_default,
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
app.add_page(pages.not_found, route=routes.NOT_FOUND)


async def initialize():
    """Initialization steps that are run once when the app starts."""
    # Note that this function is run as an asynchronous lifespan task, so the
    # application doesn't actually wait for it to be finished before starting to serve
    # requests.  So we should be careful if we ever add any longer-running steps here.

    # load config here, so we fail immediately if there is any issue with it
    load_config()

    create_default_users()


app.register_lifespan_task(initialize)
