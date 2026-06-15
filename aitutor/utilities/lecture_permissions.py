"""Helpers for lecture-specific permission and membership checks."""

from collections.abc import Collection

from sqlmodel import Session, func, select

from aitutor.models import GlobalPermission, LectureRole, LinkUserLecture


def get_user_lecture_link(
    session: Session,
    *,
    user_id: int,
    lecture_id: int,
) -> LinkUserLecture | None:
    """Return the membership link for one user and lecture, if it exists."""
    return session.exec(
        select(LinkUserLecture).where(
            LinkUserLecture.lecture_id == lecture_id,
            LinkUserLecture.user_id == user_id,
        )
    ).one_or_none()


def get_user_lecture_role(
    session: Session,
    *,
    user_id: int,
    lecture_id: int,
) -> LectureRole | None:
    """Return the user's lecture role, if they are a member of the lecture."""
    link = get_user_lecture_link(session, user_id=user_id, lecture_id=lecture_id)
    return link.role if link is not None else None


def has_global_admin_permission(
    global_permissions: Collection[GlobalPermission],
) -> bool:
    """Return whether the user has global admin permissions."""
    return GlobalPermission.ADMIN in global_permissions


def user_may_view_lecture(
    session: Session,
    *,
    user_id: int,
    global_permissions: Collection[GlobalPermission],
    lecture_id: int,
) -> bool:
    """Return whether a user may view a lecture-specific page."""
    if has_global_admin_permission(global_permissions):
        return True

    return (
        get_user_lecture_link(
            session,
            user_id=user_id,
            lecture_id=lecture_id,
        )
        is not None
    )


def user_may_edit_lecture(
    session: Session,
    *,
    user_id: int,
    global_permissions: Collection[GlobalPermission],
    lecture_id: int,
) -> bool:
    """Return whether a user may edit a lecture's settings."""
    return has_global_admin_permission(global_permissions) or (
        get_user_lecture_role(
            session,
            user_id=user_id,
            lecture_id=lecture_id,
        )
        == LectureRole.OWNER
    )


def count_lecture_owners(session: Session, *, lecture_id: int) -> int:
    """Return the number of owners for one lecture."""
    return session.exec(
        select(func.count()).where(
            LinkUserLecture.lecture_id == lecture_id,
            LinkUserLecture.role == LectureRole.OWNER,
        )
    ).one()
