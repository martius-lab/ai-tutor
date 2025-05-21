"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import reflex as rx
from aitutor import pages
from aitutor.auth.pages import custom_login_page, custom_register_page
from aitutor.config import load_config
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
app.add_page(pages.add_exercises_default, route=routes.ADD_EXERCISE)
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


# load config here, so we fail immediately if there is any issue with it
load_config()

# catch error if db is not created yet
try:
    create_default_users()
except Exception as e:
    print(f"Default users could not be created: {e}")
