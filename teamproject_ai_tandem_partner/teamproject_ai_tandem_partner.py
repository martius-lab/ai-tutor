"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx


from . import pages  # Imports components and pages


class State(rx.State):
    """The app state."""

    ...


app = rx.App()
app.add_page(pages.home_page_default, route="/")
app.add_page(pages.settings_default, route="/settings")
app.add_page(pages.login_default, route="/login")
app.add_page(pages.user_profile_default, route="/profile")
