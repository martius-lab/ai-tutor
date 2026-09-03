"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import fcntl
import sys

import reflex as rx

import aitutor.routes as routes
from aitutor import pages
from aitutor.config import get_config
from aitutor.env_settings import get_env_settings
from aitutor.utilities.cprint import cprint
from aitutor.utilities.first_setup import first_time_setup

app = rx.App()
# info: add dynamic routes first
app.add_page(
    pages.finished_view_tutor_page,
    route=routes.FINISHED_VIEW_TUTOR + "/[exercise_id]/[url_user_id]",
    on_load=pages.FinishedViewTutorState.on_load,
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
    pages.lecture_prompts_page,
    route=routes.LECTURE_PROMPTS + "/[lecture_id]",
    on_load=pages.LectureManagePromptsState.on_load,
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
    pages.lecture_token_analyzer_page,
    route=routes.LECTURE_TOKEN_ANALYZER + "/[lecture_id]",
    on_load=pages.LectureTokenAnalyzerState.on_load,
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
    pages.home_page,
    route=routes.HOME,
    on_load=pages.HomeState.on_load,
)
app.add_page(
    pages.manage_users_page,
    route=routes.MANAGE_USERS,
    on_load=pages.ManageUsersState.on_load,
)
app.add_page(
    pages.configuration_page,
    route=routes.CONFIGURATION,
    on_load=[
        pages.ManageConfigState.on_load,
        pages.LecturerRegistrationTokenState.on_load,
    ],
)
app.add_page(
    pages.prompts_page,
    route=routes.PROMPTS,
    on_load=pages.ManagePromptsState.on_load,
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


class Lock:
    """File-based lock to avoid race conditions between workers."""

    # taken from https://stackoverflow.com/a/60214222
    def __enter__(self):
        self.fp = open("/tmp/aitutor-initialization.lock", "wb")
        fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX)

    def __exit__(self, _type, value, tb):
        fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
        self.fp.close()


def initialize():
    """Initialization steps that are run once when the app starts."""

    print("Executing initialization tasks")

    with Lock():
        # Ensure the application is set up correctly.  Needs a lock to avoid race
        # conditions when using multiple workers.
        first_time_setup()

    # load config here, so we fail immediately if there is any issue with it
    try:
        _ = get_config()
    except Exception as e:
        cprint(f"Error loading config: {e}", fg="white", bg="red")
        sys.exit(1)

    try:
        settings = get_env_settings()
    except ValueError as e:
        cprint(f"Error loading settings: {e}", fg="white", bg="red")
        sys.exit(1)

    if settings.OPENAI_BASE_URL:
        print(f"Using OPENAI_BASE_URL={settings.OPENAI_BASE_URL}")

    if not settings.SMTP:
        cprint(
            "Warning: SMTP is not configured. Emails will not be sent.",
            fg="yellow",
        )

    cprint("Initialization tasks completed.", fg="green")


app.register_lifespan_task(initialize)
