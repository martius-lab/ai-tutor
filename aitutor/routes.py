"""
Defines the routes used in the AI Tutor application.
"""

import reflex_local_auth

HOME = "/"
CHAT = "/chat"  # needs to be /chat/[exercise_id] to work
EXERCISES = "/exercises"
MANAGE_EXERCISES = "/manage_exercises"
MANAGE_USERS = "/manage_users"
NOT_FOUND = "/404"
FINISHED_VIEW = "/finished_view"  # needs to be /finished_view/[exercise_id] to work
SUBMISSIONS = "/submissions"
USER_SETTINGS = "/user_settings"

# needs to be /finished_view_tutor/[exercise_id]/[url_user_id]
FINISHED_VIEW_TUTOR = "/finished_view_tutor"

IMPRESSUM = "/impressum"
PRIVACY_NOTICE = "/privacy_notice"

# we use the routes from reflex_local_auth to be
# able to use functions like Loginstate.redir
LOGIN = reflex_local_auth.routes.LOGIN_ROUTE
REGISTER = reflex_local_auth.routes.REGISTER_ROUTE
