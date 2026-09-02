"""Utility functions for first-time setup of the application."""

import reflex as rx
from reflex_local_auth.user import LocalUser
from sqlmodel import select

from aitutor.config import (
    get_default_admin_user,
    get_default_config,
    get_default_prompts,
)
from aitutor.models import (
    Config,
    GlobalPermission,
    Permission,
    Prompt,
    UserInfo,
    UserRole,
)


def first_time_setup():
    """Perform first-time setup of the application."""
    initialize_config_db()
    add_default_prompts_to_db()
    create_default_admin_user()


def initialize_config_db():
    """ensure there is a config row in the database."""
    with rx.session() as session:
        if not session.get(Config, 1):
            config = get_default_config()
            session.add(config)
            session.commit()
            print("Configuration added to the database.")


def add_default_prompts_to_db():
    """Add default prompts to the database."""
    with rx.session() as session:
        _prompt = session.exec(
            select(Prompt).where(Prompt.lecture_id == None)  # noqa: E711
        ).first()
        if _prompt:
            return

        print("No prompts found in the database. Adding default prompts...")
        for prompt_values in get_default_prompts():
            prompt = Prompt(
                **prompt_values,
                lecture_id=None,
            )
            session.add(prompt)
            print(f"Added prompt '{prompt.name}' to the database.")

        session.commit()


def create_default_admin_user():
    """Create default admin user."""
    user = get_default_admin_user()

    with rx.session() as session:
        # Abort if any user already exists.  This is only for creating the initial admin
        # user.
        existing_user = session.exec(select(LocalUser)).first()
        if existing_user:
            return

        new_user = LocalUser(
            username=user["name"],
            password_hash=LocalUser.hash_password(user["password"]),
            enabled=True,
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        if new_user.id is None:
            raise ValueError("Failed to create admin user: user ID is None.")

        session.add(
            UserInfo(
                email=user["email"],
                role=UserRole.ADMIN,
                user_id=new_user.id,
            )
        )
        session.add(Permission(user_id=new_user.id, permission=GlobalPermission.ADMIN))

        session.commit()
        print(
            f"Created default user '{user['name']}' with password '{user['password']}'"
            " -- CHANGE THE PASSWORD IMMEDIATELY!"
        )
