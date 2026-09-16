"""Periodic cleanup of email verification data and unverified accounts."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from reflex_local_auth.auth_session import LocalAuthSession
from reflex_local_auth.user import LocalUser
from sqlmodel import Session, select

from aitutor.global_vars import TIME_ZONE, UNVERIFIED_ACCOUNT_RETENTION
from aitutor.models import LectureRole, LinkUserLecture, UserInfo, VerificationToken


def _reference_time(now: datetime | None) -> datetime:
    """
    Return the reference time for comparisons with timestamps in the database.

    The result is always in TIME_ZONE.  This matters for SQLite, which drops the time
    zone of a datetime *without converting it* when binding it to a query.  The stored
    timestamps have been written in TIME_ZONE as well, so their wall clock times are
    only comparable to a reference time in that time zone.

    Args:
        now: The reference time (timezone-aware) or None for the current time.

    Raises:
        ValueError: If ``now`` is a naive datetime.
    """
    if now is None:
        return datetime.now(ZoneInfo(TIME_ZONE))
    if now.tzinfo is None:
        raise ValueError("The reference time must be timezone-aware.")
    return now.astimezone(ZoneInfo(TIME_ZONE))


@dataclass(frozen=True)
class AccountSummary:
    """The data of an account that is worth reporting about it."""

    user_id: int
    username: str
    email: str
    created_at: datetime


@dataclass
class UnverifiedAccountCleanupResult:
    """Outcome of :func:`delete_unverified_accounts`."""

    #: Accounts that have been deleted.
    deleted: list[AccountSummary]
    #: Accounts that are due for deletion but have been kept because they are the only
    #: owner of a lecture.  These need to be looked at by an admin.
    skipped_sole_lecture_owner: list[AccountSummary]


def purge_expired_tokens(session: Session, *, now: datetime | None = None) -> int:
    """
    Delete all verification tokens that have expired, regardless of their purpose.

    Note that the caller is responsible for committing the session.

    Args:
        session: Database session.  Not committed by this function.
        now: Reference time (timezone-aware), defaults to the current time.

    Returns:
        The number of deleted tokens.
    """
    now = _reference_time(now)

    expired = session.exec(
        select(VerificationToken).where(VerificationToken.expires_at < now)
    ).all()
    for token in expired:
        session.delete(token)

    return len(expired)


def delete_unverified_accounts(
    session: Session, *, now: datetime | None = None
) -> UnverifiedAccountCleanupResult:
    """
    Delete accounts whose email address has not been confirmed in time.

    An account is deleted if it is not verified and was created more than
    ``UNVERIFIED_ACCOUNT_RETENTION`` ago.  Since ``UserInfo.verified`` never flips back
    to False (an address change is only a *pending* change), this cannot hit an
    account that is in use.

    As in the user management, an account that is the only owner of a lecture is not
    deleted (this should not happen for an account that could never log in, but an
    admin may have made it an owner).

    Note that the caller is responsible for committing the session.

    Args:
        session: Database session.  Not committed by this function.
        now: Reference time (timezone-aware), defaults to the current time.

    Returns:
        Which accounts have been deleted and which have been skipped.
    """
    cutoff = _reference_time(now) - UNVERIFIED_ACCOUNT_RETENTION

    result = UnverifiedAccountCleanupResult(deleted=[], skipped_sole_lecture_owner=[])

    rows = session.exec(
        select(LocalUser, UserInfo)
        .join(UserInfo)
        .where(
            UserInfo.verified == False,  # noqa: E712
            UserInfo.created_at < cutoff,
        )
        .order_by(LocalUser.id)  # type: ignore
    ).all()

    for local_user, user_info in rows:
        assert local_user.id is not None
        summary = AccountSummary(
            user_id=local_user.id,
            username=local_user.username,
            email=user_info.email,
            created_at=user_info.created_at,
        )

        if _is_sole_owner_of_a_lecture(session, local_user.id):
            result.skipped_sole_lecture_owner.append(summary)
            continue

        _delete_account(session, local_user)
        result.deleted.append(summary)

    return result


def _is_sole_owner_of_a_lecture(session: Session, user_id: int) -> bool:
    """Check whether the user is the only owner of at least one lecture."""
    owner_links = session.exec(
        select(LinkUserLecture).where(
            LinkUserLecture.user_id == user_id,
            LinkUserLecture.role == LectureRole.OWNER,
        )
    ).all()

    for owner_link in owner_links:
        other_owner = session.exec(
            select(LinkUserLecture).where(
                LinkUserLecture.lecture_id == owner_link.lecture_id,
                LinkUserLecture.user_id != user_id,
                LinkUserLecture.role == LectureRole.OWNER,
            )
        ).first()
        if other_owner is None:
            return True

    return False


def _delete_account(session: Session, local_user: LocalUser):
    """Delete an account."""
    # LocalAuthSession doesn't have a foreign key relationship, so needs to be deleted
    # explicitly.  Everything else should be cascade-deleted when deleting local_user.
    for auth_session in session.exec(
        select(LocalAuthSession).where(LocalAuthSession.user_id == local_user.id)
    ).all():
        session.delete(auth_session)

    session.delete(local_user)
