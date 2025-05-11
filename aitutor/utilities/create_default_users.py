"""
Provides a utility function to create default users with specific roles

It interacts with the database to check for an existing user with that role
and creates one with default credentials if necessary.
"""

from aitutor.models import UserInfo, UserRole
import reflex as rx
from sqlmodel import select
from reflex_local_auth.user import LocalUser
import tomli

with open("config.toml", "rb") as f:
    config = tomli.load(f)
config = config["defaultusers"]

# admin information
admin_role: UserRole = UserRole.ADMIN
admin_name = config["admin_name"]
admin_password = config["admin_password"]
admin_email = config["admin_email"]

# teacher information
teacher_role: UserRole = UserRole.TEACHER
teacher_name = config["teacher_name"]
teacher_password = config["teacher_password"]
teacher_email = config["teacher_email"]

# student information
student_role: UserRole = UserRole.STUDENT
student_name = config["student_name"]
student_password = config["student_password"]
student_email = config["student_email"]


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

        new_user = LocalUser()
        new_user.username = name
        new_user.password_hash = LocalUser.hash_password(password)
        new_user.enabled = True
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
    """
    Create default users (admin, teacher and student) if a user with that role
    does not already exist.
    """
    create_user_if_not_exists(
        role=admin_role,
        name=admin_name,
        password=admin_password,
        email=admin_email,
    )
    create_user_if_not_exists(
        role=teacher_role,
        name=teacher_name,
        password=teacher_password,
        email=teacher_email,
    )
    create_user_if_not_exists(
        role=student_role,
        name=student_name,
        password=student_password,
        email=student_email,
    )
