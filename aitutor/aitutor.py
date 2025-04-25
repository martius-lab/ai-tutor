"""AI-Tutor Reflex app.

This module contains the main app definition for Reflex.
"""

import reflex as rx
import reflex_local_auth
from aitutor import pages
from aitutor.auth.pages import custom_login_page, custom_register_page
from aitutor.pages.exercises import ExercisesState
from aitutor.utilities.create_admin_user import create_admin_if_not_exists

app = rx.App()
app.add_page(pages.home_default, route="/")
app.add_page(pages.chat_default, route="/chat")
app.add_page(pages.add_exercises_default, route="/add-exercises")
app.add_page(
    pages.exercises_default,
    route="/exercises",
    on_load=ExercisesState.fetch_exercises,
)
# reflex_local_auth pages
app.add_page(
    custom_login_page,
    route=reflex_local_auth.routes.LOGIN_ROUTE,
    title="Login",
)
app.add_page(
    custom_register_page,
    route=reflex_local_auth.routes.REGISTER_ROUTE,
    title="Register",
)

# catch error if db is not created yet
try:
    create_admin_if_not_exists()
except Exception as e:
    print(f"Admin could not be created: {e}")

