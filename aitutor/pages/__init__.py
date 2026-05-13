from aitutor.pages.beta_ai_chat.page import beta_ai_chat_page
from aitutor.pages.beta_ai_chat.state import BetaAIChatState
from aitutor.pages.beta_ai_diagnosis_lab.page import beta_ai_diagnosis_lab_page
from aitutor.pages.beta_ai_diagnosis_lab.state import BetaAIDiagnosisLabState
from aitutor.pages.beta_ai_exercises.page import beta_ai_exercises_page
from aitutor.pages.beta_ai_exercises.state import BetaAIExercisesState
from aitutor.pages.beta_ai_student_exercises.page import beta_ai_student_exercises_page
from aitutor.pages.beta_ai_student_exercises.state import BetaAIStudentExercisesState
from aitutor.pages.beta_ai_trace_logs.page import beta_ai_trace_logs_page
from aitutor.pages.beta_ai_trace_logs.state import BetaAITraceLogsState
from aitutor.pages.chat.page import chat_page
from aitutor.pages.chat.state import ChatState
from aitutor.pages.configuration.page import configuration_page
from aitutor.pages.configuration.state import ManageConfigState
from aitutor.pages.exercises.page import exercises_page
from aitutor.pages.exercises.state import ExercisesState
from aitutor.pages.finished_view.page import finished_view_page
from aitutor.pages.finished_view.state import FinishedViewState
from aitutor.pages.finished_view_tutor.page import finished_view_tutor_page
from aitutor.pages.finished_view_tutor.state import FinishedViewTutorState
from aitutor.pages.home.page import home_page
from aitutor.pages.home.state import HomeState
from aitutor.pages.legal_infos.page import impressum_page, privacy_notice_page
from aitutor.pages.login_and_registration.page import (
    custom_login_page,
    custom_register_page,
)
from aitutor.pages.login_and_registration.state import MyLoginState, MyRegisterState
from aitutor.pages.manage_exercises.page import manage_exercises_page
from aitutor.pages.manage_exercises.state import ManageExercisesState, ManageTagsState
from aitutor.pages.manage_users.page import manage_users_page
from aitutor.pages.manage_users.state import ManageUsersState
from aitutor.pages.navbar import navbar
from aitutor.pages.not_found.page import not_found_page
from aitutor.pages.prompts.page import prompts_page
from aitutor.pages.prompts.state import ManagePromptsState
from aitutor.pages.report_view.page import report_view_page
from aitutor.pages.report_view.state import ReportViewState
from aitutor.pages.reports.page import reports_page
from aitutor.pages.reports.state import ReportsState
from aitutor.pages.submissions.page import submissions_page
from aitutor.pages.submissions.state import SubmissionsState
from aitutor.pages.token_analyzer.page import token_analyzer_page
from aitutor.pages.token_analyzer.state import TokenAnalyzerState
from aitutor.pages.user_settings.page import user_settings_page
from aitutor.pages.user_settings.state import UserSettingsState

__all__ = [
    # pages
    "chat_page",
    "beta_ai_chat_page",
    "beta_ai_diagnosis_lab_page",
    "beta_ai_exercises_page",
    "beta_ai_student_exercises_page",
    "beta_ai_trace_logs_page",
    "home_page",
    "manage_exercises_page",
    "manage_users_page",
    "exercises_page",
    "navbar",
    "not_found_page",
    "prompts_page",
    "finished_view_page",
    "submissions_page",
    "finished_view_tutor_page",
    "custom_login_page",
    "custom_register_page",
    "impressum_page",
    "privacy_notice_page",
    "user_settings_page",
    "configuration_page",
    "token_analyzer_page",
    "reports_page",
    "report_view_page",
    # states
    "ChatState",
    "BetaAIChatState",
    "BetaAIDiagnosisLabState",
    "BetaAIExercisesState",
    "BetaAIStudentExercisesState",
    "BetaAITraceLogsState",
    "HomeState",
    "ExercisesState",
    "FinishedViewState",
    "FinishedViewTutorState",
    "ManageExercisesState",
    "ManageTagsState",
    "ManageUsersState",
    "SubmissionsState",
    "MyLoginState",
    "MyRegisterState",
    "UserSettingsState",
    "ManageConfigState",
    "ReportsState",
    "ReportViewState",
    "ManagePromptsState",
    "TokenAnalyzerState",
]
