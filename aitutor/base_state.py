"""Check sessions status, authenticate sessions, destroy sessions accordingly"""

import datetime

from sqlalchemy.exc import OperationalError

from .auth_session import AuthSession
from .models import User

import reflex as rx
import secrets

from sqlmodel import select

AUTH_TOKEN_LOCAL_STORAGE_KEY = "_auth_tokens"
DEFAULT_AUTH_SESSION_EXPIRATION_DELTA = datetime.timedelta(days=7)


class State(rx.State):
    """Authenticate, logout or login accordingly."""

    # auth_token is stored in local storage to persist across tab and browser sessions
    auth_token: str = rx.LocalStorage(name=AUTH_TOKEN_LOCAL_STORAGE_KEY)

    @rx.var
    def authenticated_user(self) -> User:
        """The currently authenticated user, or a dummy user if not authenticated.

        Returns:
            A User instance with id=-1 if not authenticated, or the User instance
            corresponding to the currently authenticated user.
        """
        try:
            with rx.session() as session:
                result = session.exec(
                    select(User, AuthSession).where(
                        AuthSession.session_id == self.auth_token,
                        AuthSession.expiration
                        >= datetime.datetime.now(datetime.timezone.utc),
                        User.id == AuthSession.user_id,
                    ),
                ).first()
                if result:
                    user, session = result
                    return user
        except OperationalError:
            return User(id=-1)
        return User(id=-1)  # type: ignore

    @rx.var
    def is_authenticated(self) -> bool:
        """Check if current user is authenticated."""
        return self.authenticated_user.id >= 0

    def do_logout(self) -> None:
        """Logout user by destroying AuthSessions associated with the auth_token."""
        with rx.session() as session:
            for auth_session in session.exec(
                select(AuthSession).where(AuthSession.session_id == self.auth_token)
            ):
                session.delete(auth_session)
            session.commit()

    def _login(
        self,
        user_id: int,
        expiration_delta: datetime.timedelta = DEFAULT_AUTH_SESSION_EXPIRATION_DELTA,
    ) -> None:
        """Create an AuthSession for the given user_id.

        If the auth_token is already associated with an AuthSession, it will be
        logged out first.

        Args:
            user_id: The user ID to associate with the AuthSession.
            expiration_delta: The amount of time before the AuthSession expires.
        """
        # already authenticated -> logout
        if self.is_authenticated:
            self.do_logout()

        if user_id < 0:
            return

        # create token with secrets
        if not self.auth_token:
            self.auth_token = secrets.token_hex(32)

        # add authenticated session to DB.
        with rx.session() as session:
            session.add(
                AuthSession(  # type: ignore
                    user_id=user_id,
                    session_id=self.auth_token,
                    expiration=datetime.datetime.now(datetime.timezone.utc)
                    + expiration_delta,
                )
            )
            session.commit()
