"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import sys
import decouple

import reflex as rx

from aitutor import pages
from aitutor.config import get_config
from aitutor.utilities.create_default_users import create_default_users
import aitutor.routes as routes

# info: add dynamic routes first
app = rx.App()
app.add_page(
    pages.finished_view_tutor_page,
    route=routes.FINISHED_VIEW_TUTOR + "/[exercise_id]/[url_user_id]",
    on_load=pages.FinishedViewTutorState.on_load,
)
app.add_page(
    pages.chat_page,
    route=routes.CHAT + "/[exercise_id]",
    on_load=pages.ChatState.on_load,
)
app.add_page(
    pages.finished_view_page,
    route=routes.FINISHED_VIEW + "/[exercise_id]",
    on_load=pages.FinishedViewState.on_load,
)
app.add_page(
    pages.submissions_page,
    route=routes.SUBMISSIONS,
    on_load=pages.SubmissionsState.on_load,
)
app.add_page(
    pages.home_page,
    route=routes.HOME,
    on_load=pages.HomeState.on_load,
)
app.add_page(
    pages.manage_exercises_page,
    route=routes.MANAGE_EXERCISES,
    on_load=pages.ManageExercisesState.on_load,
)
app.add_page(
    pages.manage_users_page,
    route=routes.MANAGE_USERS,
    on_load=pages.ManageUsersState.on_load,
)
app.add_page(
    pages.configuration_page,
    route=routes.CONFIGURATION,
    on_load=pages.ConfigurationState.on_load,
)
app.add_page(
    pages.exercises_page,
    route=routes.EXERCISES,
    on_load=pages.ExercisesState.on_load,
)
app.add_page(
    pages.user_settings_page,
    route=routes.USER_SETTINGS,
)

# reflex_local_auth pages
app.add_page(
    pages.custom_login_page,
    route=routes.LOGIN,
    on_load=pages.MyLoginState.on_load,
)
app.add_page(
    pages.custom_register_page,
    route=routes.REGISTER,
    on_load=pages.MyRegisterState.on_load,
)
app.add_page(pages.not_found_page, route=routes.NOT_FOUND)
app.add_page(pages.impressum_page, route=routes.IMPRESSUM)
app.add_page(pages.privacy_notice_page, route=routes.PRIVACY_NOTICE)


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
