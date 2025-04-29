"""
Provides a utility function to create default users with specific roles

It interacts with the database to check for an existing user with that role
and creates one with default credentials if necessary.
"""

from aitutor.auth.models import UserInfo, UserRole
import reflex as rx
from sqlmodel import select
from reflex_local_auth.user import LocalUser


# admin information
admin_role: UserRole = UserRole.ADMIN
admin_name = "admin"
admin_password = "sehrgeheim"
admin_email = "admin@mail.de"

# teacher information
teacher_role: UserRole = UserRole.TEACHER
teacher_name = "teacher"
teacher_password = "geheim"
teacher_email = "teacher@mail.de"

# student information
student_role: UserRole = UserRole.STUDENT
student_name = "student"
student_password = "lol"
student_email = "student@mail.de"


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
