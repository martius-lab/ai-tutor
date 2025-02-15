"""retrieve the users role"""

from aitandem.auth_session import AuthSession
from sqlmodel import select
from aitandem.components.error_box import error_popup
from aitandem.models import User
import reflex as rx


class RoleNotFoundError(Exception):
    """Custom exception for unknown roles"""

    pass


def get_user_role(session_id: str) -> str:
    """
    retrieve the users role based on the session id
    Args:
        session_id (str): The users session id
    Returns:
        str: The users role ("student" or "teacher"), or an error
    """
    with rx.session() as session:
        # find user ID based on session ID
        auth_session = session.exec(
            select(AuthSession).where(AuthSession.id == session_id)
        ).first()

        if auth_session:
            # get user from user ID
            user = session.exec(
                select(User).where(User.id == auth_session.user_id)
            ).first()

            if user:
                return user.role  # if it exists, return the role
            else:
                error_popup("User not found!")
                raise RoleNotFoundError(
                    "Cannot find user associated with this session!"
                )
        else:
            error_popup("Invalid session!")
            raise RoleNotFoundError("No valid session found!")
