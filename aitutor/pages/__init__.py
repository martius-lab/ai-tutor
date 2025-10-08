from aitutor.pages.chat.page import chat_page
from aitutor.pages.exercises.page import exercises_page
from aitutor.pages.finished_view.page import finished_view_page
from aitutor.pages.home.page import home_page
from aitutor.pages.manage_exercises.page import manage_exercises_page
from aitutor.pages.manage_users.page import manage_users_page
from aitutor.pages.not_found.page import not_found_page
from aitutor.pages.navbar import navbar
from aitutor.pages.submissions.page import submissions_page
from aitutor.pages.finished_view_tutor.page import finished_view_tutor_page
from aitutor.pages.login_and_registration.page import (
    custom_login_page,
    custom_register_page,
)
from aitutor.pages.legal_infos.page import impressum_page, privacy_notice_page

from aitutor.pages.chat.state import ChatState
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.home.state import HomeState
from aitutor.pages.finished_view_tutor.state import FinishedViewTutorState
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.manage_users.state import ManageUsersState
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.pages.login_and_registration.state import MyLoginState, MyRegisterState

__all__ = [
    # pages
    "chat_page",
    "home_page",
    "manage_exercises_page",
    "manage_users_page",
    "exercises_page",
    "navbar",
    "not_found_page",
    "finished_view_page",
    "submissions_page",
    "finished_view_tutor_page",
    "custom_login_page",
    "custom_register_page",
    "impressum_page",
    "privacy_notice_page",
    # states
    "ChatState",
    "HomeState",
    "ExercisesState",
    "FinishedViewState",
    "FinishedViewTutorState",
    "ManageExercisesState",
    "ManageUsersState",
    "SubmissionsState",
    "MyLoginState",
    "MyRegisterState",
]
