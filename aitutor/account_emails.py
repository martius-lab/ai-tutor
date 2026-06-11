"""Account welcome email and password reset helpers."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Optional, cast

from decouple import config
from reflex_local_auth.auth_session import LocalAuthSession
from reflex_local_auth.user import LocalUser
from sqlmodel import Column, DateTime, Field, Session, SQLModel, col, select

from aitutor.mail import SmtpSettings, send_text_email
from aitutor.models import UserInfo

PASSWORD_RESET = "password_reset"
PASSWORD_RESET_TTL_HOURS = 2


class AccountEmailToken(SQLModel, table=True):
    """Hashed one-time account email token."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="localuser.id", nullable=False, ondelete="CASCADE", index=True
    )
    purpose: str = Field(nullable=False, index=True)
    token_hash: str = Field(nullable=False, unique=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    used_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


def public_base_url() -> str:
    """Public base URL used for links in account emails."""
    return cast(
        str, config("AITUTOR_PUBLIC_URL", default="http://localhost:3000", cast=str)
    ).rstrip("/")


def hash_token(token: str) -> str:
    """Return the irreversible hash stored for a one-time token."""
    return sha256(token.encode("utf-8")).hexdigest()


def create_account_token(
    session: Session, *, user_id: int, purpose: str, ttl_hours: int
) -> str:
    """Create a one-time account token and store only its hash."""
    token = token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session.add(
        AccountEmailToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_token(token),
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )
    )
    return token


def get_valid_token(
    session: Session, *, token: str, purpose: str
) -> AccountEmailToken | None:
    """Return a valid unused token row, if any."""
    token_row = session.exec(
        select(AccountEmailToken).where(
            AccountEmailToken.token_hash == hash_token(token),
            AccountEmailToken.purpose == purpose,
            col(AccountEmailToken.used_at).is_(None),
        )
    ).one_or_none()
    if token_row is None:
        return None
    if token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    return token_row


def build_password_reset_link(token: str) -> str:
    """Build a password reset link."""
    return f"{public_base_url()}/reset_password/{token}"


def send_signup_welcome(*, local_user: LocalUser, user_info: UserInfo) -> None:
    """Send a welcome email for a newly registered account."""
    from aitutor.language_state import BackendTranslations as BT

    if local_user.id is None:
        raise ValueError("Cannot send welcome email before user is persisted.")
    login_url = f"{public_base_url()}/login"
    send_text_email(
        to_email=user_info.email,
        subject=BT.signup_welcome_subject(user_info.language),
        body=BT.signup_welcome_body(
            user_info.language,
            username=local_user.username,
            login_url=login_url,
        ),
    )


def send_password_reset(session: Session, *, identifier: str) -> None:
    """Send a password reset email if the username or email exists."""
    from aitutor.language_state import BackendTranslations as BT

    settings = SmtpSettings.from_env()
    row = session.exec(
        select(LocalUser, UserInfo)
        .join(UserInfo, col(UserInfo.user_id) == col(LocalUser.id))
        .where(
            (col(LocalUser.username) == identifier)
            | (col(UserInfo.email) == identifier)
        )
    ).one_or_none()
    if row is None:
        return

    local_user, user_info = row
    if local_user.id is None:
        return

    token = create_account_token(
        session,
        user_id=local_user.id,
        purpose=PASSWORD_RESET,
        ttl_hours=PASSWORD_RESET_TTL_HOURS,
    )
    link = build_password_reset_link(token)
    send_text_email(
        to_email=user_info.email,
        subject=BT.password_reset_subject(user_info.language),
        body=BT.password_reset_body(
            user_info.language,
            username=local_user.username,
            reset_link=link,
            ttl_hours=PASSWORD_RESET_TTL_HOURS,
        ),
        settings=settings,
    )


def reset_password(session: Session, *, token: str, new_password: str) -> bool:
    """Reset a user's password from a valid token and clear active sessions."""
    token_row = get_valid_token(session, token=token, purpose=PASSWORD_RESET)
    if token_row is None:
        return False

    local_user = session.get(LocalUser, token_row.user_id)
    if local_user is None:
        return False

    now = datetime.now(timezone.utc)
    local_user.password_hash = LocalUser.hash_password(new_password)
    local_user.enabled = True
    token_row.used_at = now

    sessions = session.exec(
        select(LocalAuthSession).where(LocalAuthSession.user_id == token_row.user_id)
    ).all()
    for auth_session in sessions:
        session.delete(auth_session)
    return True
