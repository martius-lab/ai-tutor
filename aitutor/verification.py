"""Issuing of verification tokens that are sent to users by email."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from aitutor.global_vars import TIME_ZONE, VERIFICATION_TOKEN_VALIDITY
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
