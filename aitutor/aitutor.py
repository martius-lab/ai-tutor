"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import fcntl
import sys

import reflex as rx

from aitutor import routes
from aitutor.config import get_config
from aitutor.env_settings import get_env_settings
from aitutor.pages.all_lectures.page import all_lectures_page
from aitutor.pages.all_lectures.state import AllLecturesState
from aitutor.pages.chat.page import chat_page
from aitutor.pages.chat.state import ChatState
from aitutor.pages.configuration.page import configuration_page
from aitutor.pages.configuration.state import (
    LecturerRegistrationTokenState,
    ManageConfigState,
)
from aitutor.pages.edit_lecture.page import edit_lecture_page
from aitutor.pages.edit_lecture.state import EditLectureState
from aitutor.pages.finished_view.page import finished_view_page
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.finished_view_tutor.page import finished_view_tutor_page
from aitutor.pages.finished_view_tutor.state import FinishedViewTutorState
from aitutor.pages.home.page import home_page
from aitutor.pages.home.state import HomeState
from aitutor.pages.lecture_exercises.page import lecture_exercises_page
from aitutor.pages.lecture_exercises.state import LectureExercisesState
from aitutor.pages.lecture_manage_exercises.page import lecture_manage_exercises_page
from aitutor.pages.lecture_manage_exercises.state import LectureManageExercisesState
from aitutor.pages.lecture_members.page import lecture_members_page
from aitutor.pages.lecture_members.state import LectureMembersState
from aitutor.pages.lecture_overview.page import lecture_overview_page
from aitutor.pages.lecture_overview.state import LectureOverviewState
from aitutor.pages.lecture_prompts.page import lecture_prompts_page
from aitutor.pages.lecture_prompts.state import LectureManagePromptsState
from aitutor.pages.lecture_report_view.page import lecture_report_view_page
from aitutor.pages.lecture_report_view.state import LectureReportViewState
from aitutor.pages.lecture_reports.page import lecture_reports_page
from aitutor.pages.lecture_reports.state import LectureReportsState
from aitutor.pages.lecture_submissions.page import lecture_submissions_page
from aitutor.pages.lecture_submissions.state import LectureSubmissionsState
from aitutor.pages.lecture_token_analyzer.page import lecture_token_analyzer_page
from aitutor.pages.lecture_token_analyzer.state import LectureTokenAnalyzerState
from aitutor.pages.legal_infos.page import impressum_page, privacy_notice_page
from aitutor.pages.login_and_registration.page import (
    custom_login_page,
    custom_register_page,
)
from aitutor.pages.login_and_registration.state import MyLoginState, MyRegisterState
from aitutor.pages.manage_users.page import manage_users_page
from aitutor.pages.manage_users.state import ManageUsersState
from aitutor.pages.my_lectures.page import my_lectures_page
from aitutor.pages.my_lectures.state import MyLecturesState
from aitutor.pages.not_found.page import not_found_page
from aitutor.pages.prompts.page import prompts_page
from aitutor.pages.prompts.state import ManagePromptsState
from aitutor.pages.user_settings.page import user_settings_page
from aitutor.utilities.cprint import cprint
from aitutor.utilities.first_setup import first_time_setup

app = rx.App()
# info: add dynamic routes first
app.add_page(
    finished_view_tutor_page,
    route=routes.FINISHED_VIEW_TUTOR + "/[exercise_id]/[url_user_id]",
    on_load=FinishedViewTutorState.on_load,
)
app.add_page(
    lecture_report_view_page,
    route=routes.LECTURE_REPORT_VIEW + "/[lecture_id]/[report_id]",
    on_load=LectureReportViewState.on_load,
)
app.add_page(
    chat_page,
    route=routes.CHAT + "/[exercise_id]",
    on_load=ChatState.on_load,
)
app.add_page(
    finished_view_page,
    route=routes.FINISHED_VIEW + "/[exercise_id]",
    on_load=FinishedViewState.on_load,
)
app.add_page(
    my_lectures_page,
    route=routes.MY_LECTURES,
    on_load=MyLecturesState.on_load,
)
app.add_page(
    lecture_overview_page,
    route=routes.LECTURE_OVERVIEW + "/[lecture_id]",
    on_load=LectureOverviewState.on_load,
)
app.add_page(
    lecture_members_page,
    route=routes.LECTURE_MEMBERS + "/[lecture_id]",
    on_load=LectureMembersState.on_load,
)
app.add_page(
    lecture_exercises_page,
    route=routes.LECTURE_EXERCISES + "/[lecture_id]",
    on_load=LectureExercisesState.on_load,
)
app.add_page(
    lecture_manage_exercises_page,
    route=routes.LECTURE_MANAGE_EXERCISES + "/[lecture_id]",
    on_load=LectureManageExercisesState.on_load,
)
app.add_page(
    lecture_prompts_page,
    route=routes.LECTURE_PROMPTS + "/[lecture_id]",
    on_load=LectureManagePromptsState.on_load,
)
app.add_page(
    lecture_submissions_page,
    route=routes.LECTURE_SUBMISSIONS + "/[lecture_id]",
    on_load=LectureSubmissionsState.on_load,
)
app.add_page(
    lecture_reports_page,
    route=routes.LECTURE_REPORTS + "/[lecture_id]",
    on_load=LectureReportsState.on_load,
)
app.add_page(
    lecture_token_analyzer_page,
    route=routes.LECTURE_TOKEN_ANALYZER + "/[lecture_id]",
    on_load=LectureTokenAnalyzerState.on_load,
)
app.add_page(
    all_lectures_page,
    route=routes.ALL_LECTURES + "/[lecture_id]",
    on_load=AllLecturesState.on_load,
)
app.add_page(
    all_lectures_page,
    route=routes.ALL_LECTURES,
    on_load=AllLecturesState.on_load,
)
app.add_page(
    edit_lecture_page,
    route=routes.EDIT_LECTURE + "/[lecture_id]",
    on_load=EditLectureState.on_load,
)
app.add_page(
    home_page,
    route=routes.HOME,
    on_load=HomeState.on_load,
)
app.add_page(
    manage_users_page,
    route=routes.MANAGE_USERS,
    on_load=ManageUsersState.on_load,
)
app.add_page(
    configuration_page,
    route=routes.CONFIGURATION,
    on_load=[
        ManageConfigState.on_load,
        LecturerRegistrationTokenState.on_load,
    ],
)
app.add_page(
    prompts_page,
    route=routes.PROMPTS,
    on_load=ManagePromptsState.on_load,
)
app.add_page(
    user_settings_page,
    route=routes.USER_SETTINGS,
)

# reflex_local_auth pages
app.add_page(
    custom_login_page,
    route=routes.LOGIN,
    on_load=MyLoginState.on_load,
)
app.add_page(
    custom_register_page,
    route=routes.REGISTER,
    on_load=MyRegisterState.on_load,
)
app.add_page(not_found_page, route=routes.NOT_FOUND)
app.add_page(impressum_page, route=routes.IMPRESSUM)
app.add_page(privacy_notice_page, route=routes.PRIVACY_NOTICE)


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
