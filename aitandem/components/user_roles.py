"""Gets the users role"""

from aitandem.auth_session import AuthSession
from sqlmodel import Session

def get_user_role(session_id: str) -> str:
    with Session() as session:
        auth_session = session.get(AuthSession, session_id)
        if auth_session:
            return auth_session.role
        else:
            pass