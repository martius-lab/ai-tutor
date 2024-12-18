"""assign roles when logging in"""

import reflex as rx
from aitandem.components.user_roles import get_user_role
from aitandem.components.error_box import error_popup


def handle_student_login(session_id: str) -> rx.Component:
    """students dashboard"""
    return rx.redirect("/student_dashboard")


def handle_teacher_login(session_id: str) -> rx.Component:
    """teachers dashboard"""
    return rx.redirect("/teacher_dashboard")


def login_default() -> rx.Component:
    """Login page."""

    def handle_login(session_id: str) -> rx.Component:
        user_role = get_user_role(session_id)
        if user_role == "student":
            return handle_student_login(session_id)
        elif user_role == "teacher":
            return handle_teacher_login(session_id)
        else:
            error_popup("Unknown role!")

    return rx.box()
