"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import sys

import reflex as rx
from sqlmodel import select

import aitutor.routes as routes
from aitutor import pages
from aitutor.app_settings import get_settings
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
    pages.lecture_report_view_page,
    route=routes.LECTURE_REPORT_VIEW + "/[lecture_id]/[report_id]",
    on_load=pages.LectureReportViewState.on_load,
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
    pages.my_lectures_page,
    route=routes.MY_LECTURES,
    on_load=pages.MyLecturesState.on_load,
)
app.add_page(
    pages.lecture_overview_page,
    route=routes.LECTURE_OVERVIEW + "/[lecture_id]",
    on_load=pages.LectureOverviewState.on_load,
)
app.add_page(
    pages.lecture_members_page,
    route=routes.LECTURE_MEMBERS + "/[lecture_id]",
    on_load=pages.LectureMembersState.on_load,
)
app.add_page(
    pages.lecture_exercises_page,
    route=routes.LECTURE_EXERCISES + "/[lecture_id]",
    on_load=pages.LectureExercisesState.on_load,
)
app.add_page(
    pages.lecture_manage_exercises_page,
    route=routes.LECTURE_MANAGE_EXERCISES + "/[lecture_id]",
    on_load=pages.LectureManageExercisesState.on_load,
)
app.add_page(
    pages.lecture_submissions_page,
    route=routes.LECTURE_SUBMISSIONS + "/[lecture_id]",
    on_load=pages.LectureSubmissionsState.on_load,
)
app.add_page(
    pages.lecture_reports_page,
    route=routes.LECTURE_REPORTS + "/[lecture_id]",
    on_load=pages.LectureReportsState.on_load,
)
app.add_page(
    pages.all_lectures_page,
    route=routes.ALL_LECTURES + "/[lecture_id]",
    on_load=pages.AllLecturesState.on_load,
)
app.add_page(
    pages.all_lectures_page,
    route=routes.ALL_LECTURES,
    on_load=pages.AllLecturesState.on_load,
)
app.add_page(
    pages.edit_lecture_page,
    route=routes.EDIT_LECTURE + "/[lecture_id]",
    on_load=pages.EditLectureState.on_load,
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
    on_load=pages.TokenAnalyzerState.on_load,
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
        _ = get_config()
    except Exception as e:
        print("\033[91m" + f"Error loading config: {e}" + "\033[0m")
        sys.exit(1)

    try:
        settings = get_settings()
    except ValueError as e:
        print("\033[91m" + str(e) + "\033[0m")
        sys.exit(1)

    if settings.openai_base_url:
        print(f"Using OPENAI_BASE_URL={settings.openai_base_url}")

    create_default_users()

    with rx.session() as session:
        prompt = session.exec(select(Prompt)).first()
        if not prompt:
            print("No prompts found in the database. Adding default prompts...")
            add_configprompts_to_db()

    print("\033[92m" + "Initialization tasks completed." + "\033[0m")


app.register_lifespan_task(initialize)
