"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import sys

import decouple
import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor import pages
from aitutor.config import add_configprompts_to_db, get_config, initialize_config_db
from aitutor.models import Prompt
from aitutor.utilities.create_default_users import create_default_users

app = rx.App(
    theme=rx.theme(
        accent_color="indigo",
        gray_color="slate",
        radius="medium",
    )
)
# info: add dynamic routes first
app.add_page(
    pages.finished_view_tutor_page,
    route=routes.FINISHED_VIEW_TUTOR + "/[exercise_id]/[url_user_id]",
    on_load=pages.FinishedViewTutorState.on_load,
)
app.add_page(
    pages.report_view_page,
    route=routes.REPORT_VIEW + "/[report_id]",
    on_load=pages.ReportViewState.on_load,
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
    on_load=pages.ManageConfigState.on_load,
)
app.add_page(
    pages.prompts_page,
    route=routes.PROMPTS,
    on_load=pages.ManagePromptsState.on_load,
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
app.add_page(
    pages.reports_page,
    route=routes.REPORTS,
    on_load=pages.ReportsState.on_load,
)
app.add_page(
    pages.token_analyzer_page,
    route=routes.TOKEN_ANALYZER,
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


def initialize():
    """Initialization steps that are run once when the app starts."""

    print("Executing initialization tasks:")

    # ensure there is a config row in the database
    initialize_config_db()

    # load config here, so we fail immediately if there is any issue with it
    try:
        config = get_config()
        if config.course_name:
            print("Configuration can be loaded successfully.")
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
    else:
        print("OPENAI_API_KEY found in environment variables.")

    create_default_users()

    with rx.session() as session:
        prompt = session.exec(select(Prompt)).first()
        if not prompt:
            print("No prompts found in the database. Adding default prompts...")
            add_configprompts_to_db()

    print("\033[92m" + "Initialization tasks completed." + "\033[0m")


app.register_lifespan_task(initialize)
