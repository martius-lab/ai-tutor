"""
Defines the routes used in the AI Tutor application.
"""

import reflex_local_auth

HOME = "/"
IMPRESSUM = "/impressum"
PRIVACY_NOTICE = "/privacy_notice"

CHAT = "/chat"  # needs to be /chat/[exercise_id] to work
FINISHED_VIEW = "/finished_view"  # needs to be /finished_view/[exercise_id] to work

# needs to be /finished_view_tutor/[exercise_id]/[url_user_id]
FINISHED_VIEW_TUTOR = "/finished_view_tutor"

ADMIN_SETTINGS = "/admin_settings"
MANAGE_USERS = ADMIN_SETTINGS + "/manage_users"
CONFIGURATION = ADMIN_SETTINGS + "/configuration"
PROMPTS = ADMIN_SETTINGS + "/prompts"

USER_SETTINGS = "/user_settings"

BETA_AI = "/beta_ai"
BETA_AI_EXERCISES = BETA_AI + "/exercises"
BETA_AI_DIAGNOSIS_LAB = BETA_AI + "/diagnosis_lab"
BETA_AI_STUDENT_EXERCISES = BETA_AI + "/student_exercises"
BETA_AI_CHAT = BETA_AI + "/chat"
BETA_AI_TRACE_LOGS = BETA_AI + "/trace_logs"
BETA_AI_SUBMISSIONS = BETA_AI + "/submissions"
BETA_AI_FINISHED_VIEW = BETA_AI + "/finished_view"
BETA_AI_FINISHED_VIEW_TUTOR = BETA_AI + "/finished_view_tutor"

LECTURES = "/lectures"
MY_LECTURES = LECTURES + "/my_lectures"
ALL_LECTURES = LECTURES + "/all_lectures"
EDIT_LECTURE = LECTURES + "/edit_lecture"
LECTURE_OVERVIEW = LECTURES + "/overview"
LECTURE_EXERCISES = LECTURES + "/exercises"
LECTURE_MANAGE_EXERCISES = LECTURES + "/manage_exercises"
LECTURE_PROMPTS = LECTURES + "/prompts"
LECTURE_MEMBERS = LECTURES + "/members"
LECTURE_SUBMISSIONS = LECTURES + "/submissions"
LECTURE_REPORTS = LECTURES + "/reports"
LECTURE_REPORT_VIEW = LECTURE_REPORTS + "/report_view"
LECTURE_TOKEN_ANALYZER = LECTURES + "/token_analyzer"

NOT_FOUND = "/404"


# we use the routes from reflex_local_auth to be
# able to use functions like Loginstate.redir
LOGIN = reflex_local_auth.routes.LOGIN_ROUTE
REGISTER = reflex_local_auth.routes.REGISTER_ROUTE
