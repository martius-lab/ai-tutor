"""
The models used in the authentication system.
"""

import reflex as rx
from sqlmodel import Field
from enum import IntEnum


class UserRole(IntEnum):
    """
    Enum for user roles.
    """

    STUDENT = 1
    TEACHER = 2
    ADMIN = 3


class UserInfo(rx.Model, table=True):
    """
    Adds more attributes to a user than just name and password.
    """

    email: str
    role: UserRole
    user_id: int = Field(foreign_key="localuser.id", ondelete="CASCADE")
