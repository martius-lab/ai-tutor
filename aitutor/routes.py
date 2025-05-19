"""
Defines the routes used in the AI Tutor application.
"""

import reflex_local_auth

HOME = "/"
CHAT = "/chat"  # needs to be /chat/[exercise_id] to work
EXERCISES = "/exercises"
ADD_EXERCISE = "/add_exercise"
NOT_FOUND = "/404"

# we use the routes from reflex_local_auth to be
# able to use functions like Loginstate.redir
LOGIN = reflex_local_auth.routes.LOGIN_ROUTE
REGISTER = reflex_local_auth.routes.REGISTER_ROUTE
