"""retrieve the users role"""

from aitandem.auth_session import AuthSession
from sqlmodel import Session
from aitandem.components.error_box import error_popup


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
    with Session() as session:
        auth_session = session.get(
            AuthSession, session_id
        )  # get the current session details
        if auth_session:
            return auth_session.role
        else:
            error_popup("Unknown role!")
            raise RoleNotFoundError("The user has an invalid role!")
