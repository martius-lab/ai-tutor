from aitutor.pages.chat.page import chat_page
from aitutor.pages.exercises.page import exercises_page
from aitutor.pages.finished_view.page import finished_view_page
from aitutor.pages.home.page import home_page
from aitutor.pages.manage_exercises.page import manage_exercises_page
from aitutor.pages.not_found.page import not_found_page
from aitutor.pages.navbar import navbar
from aitutor.pages.submissions.page import submissions_page
from aitutor.pages.finished_view_teacher.page import finished_view_teacher_page

from aitutor.pages.chat.state import ChatState
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.home.state import HomeState
from aitutor.pages.finished_view_teacher.state import FinishedViewTeacherState
from aitutor.pages.manage_exercises.state import ManageExercisesState
from aitutor.pages.submissions.state import SubmissionsState

__all__ = [
    # pages
    "chat_page",
    "home_page",
    "manage_exercises_page",
    "exercises_page",
    "navbar",
    "not_found_page",
    "finished_view_page",
    "submissions_page",
    "finished_view_teacher_page",
    # states
    "ChatState",
    "HomeState",
    "ExercisesState",
    "FinishedViewState",
    "FinishedViewTeacherState",
    "ManageExercisesState",
    "SubmissionsState",
]
