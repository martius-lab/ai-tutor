"""
This module provides a utility function to create an admin user if one does not
already exist.

It interacts with the database to check for an existing admin user
and creates one with default credentials if necessary.
"""

from aitutor.auth.models import UserInfo, UserRole
import reflex as rx
from sqlmodel import select
from reflex_local_auth.user import LocalUser


# account information
userrole: UserRole = UserRole.ADMIN
username = "admin"
password = "sehrgeheim"
email = "admin@mail.de"


def create_admin_if_not_exists():
    """
    Create an admin user if one does not already exist in the database.

    This function checks for an existing admin user and, if none is found,
    creates a new admin user with default credentials.
    """
    with rx.session() as session:
        existing_admin = session.exec(
            select(UserInfo).where(UserInfo.role == userrole)
        ).first()
        if existing_admin:
            return

        new_user = LocalUser()
        new_user.username = username
        new_user.password_hash = LocalUser.hash_password(password)
        new_user.enabled = True
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        if new_user.id is None:
            raise ValueError("Failed to create admin user: user ID is None.")

        session.add(
            UserInfo(
                email=email,
                role=userrole,
                user_id=new_user.id,
            )
        )
        session.commit()
