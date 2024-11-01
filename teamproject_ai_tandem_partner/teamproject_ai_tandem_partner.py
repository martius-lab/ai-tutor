"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config

from . import components, pages

class State(rx.State):
    """The app state."""

    ...

app = rx.App()
app.add_page(pages.home_default, route='/')
app.add_page(pages.settings_default, route='/settings')
app.add_page(pages.login_default, route='/login')
app.add_page(pages.profile_default, route='/profile')