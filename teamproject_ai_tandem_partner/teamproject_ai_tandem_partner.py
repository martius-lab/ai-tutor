"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx


<<<<<<< HEAD
from . import (
    pages,
)  # ,components: Uncommented so ruff check is passed. Uncomment when using components.
=======
from . import pages  # Imports components and pages
>>>>>>> 5cca67505bdf79f2281212a51cbf46a105bc82b0


class State(rx.State):
    """The app state."""

    ...


app = rx.App()
<<<<<<< HEAD
app.add_page(pages.home_default, route="/")
app.add_page(pages.settings_default, route="/settings")
app.add_page(pages.login_default, route="/login")
app.add_page(pages.profile_default, route="/profile")
=======
app.add_page(pages.home_page_default, route="/")
app.add_page(pages.settings_default, route="/settings")
app.add_page(pages.login_default, route="/login")
app.add_page(pages.user_profile_default, route="/profile")
>>>>>>> 5cca67505bdf79f2281212a51cbf46a105bc82b0
