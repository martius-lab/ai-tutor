"""
Provides a utility function to create default users with specific roles

It interacts with the database to check for an existing user with that role
and creates one with default credentials if necessary.
"""

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlmodel import select

from aitutor.config import get_config
from aitutor.models import UserInfo, UserRole


def create_user_if_not_exists(role: UserRole, name: str, password: str, email: str):
    """
    Create a user with the given role and credentials if one does not already exist.
    """
    with rx.session() as session:
        existing_user = session.exec(
            select(UserInfo).where(UserInfo.role == role)
        ).first()
        if existing_user:
            return

        new_user = LocalUser(
            username=name, password_hash=LocalUser.hash_password(password), enabled=True
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        if new_user.id is None:
            raise ValueError(
                f"Failed to create {role.name.lower()} user: user ID is None."
            )

        session.add(
            UserInfo(
                email=email,
                role=role,
                user_id=new_user.id,
            )
        )
        session.commit()


def create_default_users():
    """Create default users, if a user with that role does not already exist."""
    for user in get_config().default_users:
        create_user_if_not_exists(
            role=UserRole[user.role.upper()],
            name=user.name,
            password=user.password,
            email=user.email,
        )
