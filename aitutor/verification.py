"""Issuing of verification tokens that are sent to users by email."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from aitutor.global_vars import (
    TIME_ZONE,
    VERIFICATION_RESEND_COOLDOWN,
    VERIFICATION_TOKEN_VALIDITY,
)
from aitutor.models import VerificationPurpose, VerificationToken


def issue_token(
    session: Session,
    *,
    user_id: int,
    email: str,
    purpose: VerificationPurpose = VerificationPurpose.EMAIL,
) -> str:
    """
    Create a verification token for the given user and return its clear text.

    There is at most one token per user and purpose, so an already existing one is
    overwritten (this is what happens when a user asks for a new verification mail).
    The clear text returned here is the only chance to see the token; only its hash is
    stored.

    Note that the caller is responsible for committing the session.

    Args:
        session: Database session.  Not committed by this function.
        user_id: ID of the ``LocalUser`` the token is issued for.
        email: The address the token is sent to.  For
            ``VerificationPurpose.EMAIL`` this is also the address that gets
            confirmed by redeeming the token, which is not necessarily the address
            currently stored in the user's ``UserInfo``.
        purpose: What the token is good for.

    Returns:
        The clear text token, to be put into the link that is sent to the user.
    """
    token = VerificationToken.generate_token()
    now = datetime.now(ZoneInfo(TIME_ZONE))

    entry = session.exec(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == purpose,
        )
    ).one_or_none()

    if entry is None:
        entry = VerificationToken(
            user_id=user_id,
            purpose=purpose,
            email=email,
            token_hash=VerificationToken.hash_token(token),
        )
        session.add(entry)
    else:
        # overwrite the existing token, thus invalidating the old one
        entry.email = email
        entry.token_hash = VerificationToken.hash_token(token)
        entry.created_at = now
        entry.used_at = None

    entry.expires_at = now + VERIFICATION_TOKEN_VALIDITY
    entry.last_sent_at = now

    return token


def resend_cooldown_remaining(
    session: Session,
    *,
    user_id: int,
    purpose: VerificationPurpose = VerificationPurpose.EMAIL,
) -> timedelta:
    """
    Return how long the user still has to wait before another mail may be sent.

    The cooldown is measured from the time the last mail was sent
    (``VerificationToken.last_sent_at``), so that it cannot be circumvented by simply
    asking for a fresh token.

    Args:
        session: Database session.
        user_id: ID of the ``LocalUser`` the token belongs to.
        purpose: What the token is good for.

    Returns:
        The remaining cooldown, or a zero timedelta if a mail may be sent right away
        (which is also the case if no token has been issued yet at all).
    """
    entry = session.exec(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == purpose,
        )
    ).one_or_none()

    if entry is None:
        return timedelta(0)

    # For comparison, both datetimes need to be timezone-aware.  Sqlite doesn't store
    # the time zone, so it gives us a naive datetime here, which is in TIME_ZONE because
    # that is what was written.  Postgres does store it and gives us an aware datetime,
    # which must be left alone.
    last_sent_at = entry.last_sent_at
    if last_sent_at.tzinfo is None:
        last_sent_at = last_sent_at.replace(tzinfo=ZoneInfo(TIME_ZONE))
    remaining = (
        last_sent_at + VERIFICATION_RESEND_COOLDOWN - datetime.now(ZoneInfo(TIME_ZONE))
    )
    return max(remaining, timedelta(0))
