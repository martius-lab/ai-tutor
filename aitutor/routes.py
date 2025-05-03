"""
Defines the routes used in the AI Tutor application.
"""

import reflex_local_auth

HOME_ROUTE = "/"
CHAT_ROUTE = "/chat"
EXERCISES_ROUTE = "/exercises"
ADD_EXERCISE_ROUTE = "/add_exercise"

# we use the routes from reflex_local_auth to be
# able to use functions like Loginstate.redir
LOGIN_ROUTE = reflex_local_auth.routes.LOGIN_ROUTE
REGISTER_ROUTE = reflex_local_auth.routes.REGISTER_ROUTE
