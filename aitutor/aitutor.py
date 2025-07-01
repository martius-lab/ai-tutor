"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import sys
import reflex as rx
import decouple
from aitutor import pages
from aitutor.auth.pages import custom_login_page, custom_register_page
from aitutor.config import get_config
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.chat.state import ChatState
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.pages.finished_view_teacher.state import FinishedViewTeacherState
from aitutor.utilities.create_default_users import create_default_users
import aitutor.routes as routes

# info: add dynamic routes first
app = rx.App()
app.add_page(
    pages.finished_view_teacher_page,
    route=routes.FINISHED_VIEW_TEACHER + "/[exercise_id]/[url_user_id]",
    on_load=FinishedViewTeacherState.on_load,
)
app.add_page(
    pages.chat_page,
    route=routes.CHAT + "/[exercise_id]",
    on_load=ChatState.on_load,
)
app.add_page(
    pages.finished_view_page,
    route=routes.FINISHED_VIEW + "/[exercise_id]",
    on_load=FinishedViewState.on_load,
)
app.add_page(
    pages.submissions_page,
    route=routes.SUBMISSIONS + "/[exercise_id]",
    on_load=SubmissionsState.on_load,
)
app.add_page(pages.home_page, route=routes.HOME)
app.add_page(
    pages.manage_exercises_page,
    route=routes.MANAGE_EXERCISES,
    on_load=ManageExercisesState.on_load,
)
app.add_page(
    pages.exercises_page,
    route=routes.EXERCISES,
    on_load=ExercisesState.on_load,
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
        config = get_config()
        print(
            f"Using {config.response_ai_model} for responses "
            + f"and {config.check_ai_model} for checks."
        )
    except Exception as e:
        print("\033[91m" + f"Error loading config: {e}" + "\033[0m")
        sys.exit(1)

    # check if an openai_key is in the .env, if not, we exit
    API_KEY = decouple.config("OPENAI_API_KEY", cast=str, default="")
    if API_KEY == "":
        print(
            "\033[91m"
            + "OPENAI_KEY is not set in the environment variables."
            + "\033[0m"
        )
        sys.exit(1)

    create_default_users()


app.register_lifespan_task(initialize)
