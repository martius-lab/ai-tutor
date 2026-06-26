"""
Defines the routes used in the AI Tutor application.
"""

import reflex_local_auth

HOME = "/"
IMPRESSUM = "/impressum"
PRIVACY_NOTICE = "/privacy_notice"

EXERCISES = "/exercises"
CHAT = "/chat"  # needs to be /chat/[exercise_id] to work
FINISHED_VIEW = "/finished_view"  # needs to be /finished_view/[exercise_id] to work

SUBMISSIONS = "/submissions"
# needs to be /finished_view_tutor/[exercise_id]/[url_user_id]
FINISHED_VIEW_TUTOR = "/finished_view_tutor"

ADMIN_SETTINGS = "/admin_settings"
MANAGE_EXERCISES = ADMIN_SETTINGS + "/manage_exercises"
MANAGE_USERS = ADMIN_SETTINGS + "/manage_users"
CONFIGURATION = ADMIN_SETTINGS + "/configuration"
PROMPTS = ADMIN_SETTINGS + "/prompts"
REPORTS = ADMIN_SETTINGS + "/reports"
TOKEN_ANALYZER = ADMIN_SETTINGS + "/token_analyzer"
# needs to be .../report_view/[report_id]
REPORT_VIEW = REPORTS + "/report_view"

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

NOT_FOUND = "/404"


# we use the routes from reflex_local_auth to be
# able to use functions like Loginstate.redir
LOGIN = reflex_local_auth.routes.LOGIN_ROUTE
REGISTER = reflex_local_auth.routes.REGISTER_ROUTE
