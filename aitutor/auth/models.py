"""
The models used in the authentication system.
"""

import reflex as rx
from sqlmodel import Field
from enum import Enum


class UserRole(str, Enum):
    """
    Enum for user roles.
    """

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class UserInfo(rx.Model, table=True):
    """
    Adds more attributes to a user than just name and password.
    """

    email: str
    role: UserRole
    user_id: int = Field(foreign_key="localuser.id", ondelete="CASCADE")
