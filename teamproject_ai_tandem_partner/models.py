"""Module defining User database model."""

import reflex as rx


class User(rx.Model):
    """db model for users"""

    user_id: int
    email: str
    passwort: str
    role: str
