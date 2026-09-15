"""Issuing and redeeming of verification tokens that are sent to users by email."""

import logging
from datetime import datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from aitutor.global_vars import (
    TIME_ZONE,
    VERIFICATION_RESEND_COOLDOWN,
    VERIFICATION_TOKEN_VALIDITY,
)
from aitutor.models import UserInfo, VerificationPurpose, VerificationToken

logger = logging.getLogger(__name__)


class RedeemResult(StrEnum):
    """Possible outcomes of redeeming an email verification token."""

    #: The address has been confirmed by this very request.
    SUCCESS = "success"
    #: The token had been used before but is still within its validity window, so the
    #: address is confirmed.  For the user this is as good as SUCCESS.
    ALREADY_USED = "already_used"
    #: The token exists but is too old to be used.
    EXPIRED = "expired"
    #: There is no such token.  It may never have existed, it may have been replaced by
    #: a newer one, or it may have been purged after expiry.
    UNKNOWN = "unknown"
    #: The token is fine, but the account it belongs to is not (see
    #: :func:`redeem_email_token`).
    ERROR = "error"


def _to_tz_aware(value: datetime) -> datetime:
    """
    Make a datetime read from the database timezone-aware.

    Sqlite does not store the time zone and thus gives us a naive datetime, which is in
    TIME_ZONE because that is what was written.  Postgres does store it and gives us an
    aware datetime, which must be left alone.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(TIME_ZONE))
    return value


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

    remaining = (
        _to_tz_aware(entry.last_sent_at)
        + VERIFICATION_RESEND_COOLDOWN
        - datetime.now(ZoneInfo(TIME_ZONE))
    )
    return max(remaining, timedelta(0))


def get_pending_email_changes(
    session: Session, *, user_id: int | None = None
) -> dict[int, str]:
    """
    Find email address changes that have not been confirmed yet.

    A change is pending if a verified account has an unused email token for an address
    other than the one currently stored on the account (see
    :func:`redeem_email_token`).  Expired tokens are included, the change is still
    outstanding until the token gets purged or replaced.

    Unverified accounts never have a pending change: their (unconfirmed) address is
    changed directly.

    Args:
        session: Database session.
        user_id: If given, only look at this user.

    Returns:
        Mapping from user ID to the address that is waiting to be confirmed.
    """
    query = (
        select(VerificationToken.user_id, VerificationToken.email)
        .join(UserInfo, UserInfo.user_id == VerificationToken.user_id)  # type: ignore
        .where(
            VerificationToken.purpose == VerificationPurpose.EMAIL,
            VerificationToken.used_at == None,
            VerificationToken.email != UserInfo.email,
            UserInfo.verified == True,  # noqa: E712
        )
    )
    if user_id is not None:
        query = query.where(VerificationToken.user_id == user_id)

    return {uid: email for uid, email in session.exec(query).all()}


def cancel_pending_email_change(session: Session, *, user_id: int) -> bool:
    """
    Drop a pending email address change of the given user, if there is one.

    The token is deleted, so the link that was sent to the new address stops working.

    Note that the caller is responsible for committing the session.

    Args:
        session: Database session.  Not committed by this function.
        user_id: ID of the ``LocalUser``.

    Returns:
        Whether there was a pending change.
    """
    if user_id not in get_pending_email_changes(session, user_id=user_id):
        return False

    entry = session.exec(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == VerificationPurpose.EMAIL,
        )
    ).one()
    session.delete(entry)
    return True


def redeem_email_token(session: Session, token: str) -> RedeemResult:
    """
    Redeem a token that confirms an email address.

    On success the address the token was issued for becomes the address of the account
    and the account is marked as verified.  The token itself is kept and only marked as
    used, so that opening the link a second time within the validity window still
    reports success -- university mail gateways tend to open every link in an incoming
    mail before the user ever gets to see it.

    Note that the caller is responsible for committing the session.

    Args:
        session: Database session.  Not committed by this function.
        token: The clear text token from the verification link.

    Returns:
        What happened, see :class:`RedeemResult`.
    """
    entry = session.exec(
        select(VerificationToken).where(
            VerificationToken.token_hash == VerificationToken.hash_token(token),
            VerificationToken.purpose == VerificationPurpose.EMAIL,
        )
    ).one_or_none()

    if entry is None:
        return RedeemResult.UNKNOWN

    now = datetime.now(ZoneInfo(TIME_ZONE))
    if now > _to_tz_aware(entry.expires_at):
        return RedeemResult.EXPIRED

    if entry.used_at is not None:
        return RedeemResult.ALREADY_USED

    user_info = session.exec(
        select(UserInfo).where(UserInfo.user_id == entry.user_id)
    ).one_or_none()

    if user_info is None:
        # Every LocalUser gets a UserInfo at registration, so this means the database is
        # inconsistent.  Nothing the user can do about it, so log it for the operators.
        logger.error(
            "ERROR: No UserInfo found for user_id=%s while redeeming an email"
            " verification token. The database is inconsistent.",
            entry.user_id,
        )
        return RedeemResult.ERROR

    # The token carries the address it confirms, which is not necessarily the one
    # currently stored on the account: an address change is modelled as a pending
    # change, leaving the old (confirmed) address in place until the new one is
    # confirmed.  For a fresh signup both are the same and this is a no-op.
    user_info.email = entry.email
    user_info.verified = True
    entry.used_at = now

    return RedeemResult.SUCCESS
