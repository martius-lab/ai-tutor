"""Utility functions related to accounts."""

from sqlalchemy.orm import aliased
from sqlmodel import Session, col, exists, select

from aitutor.models import LectureRole, LinkUserLecture


def is_sole_owner_of_a_lecture(session: Session, user_id: int) -> bool:
    """Check whether the user is the only owner of at least one lecture."""
    other_owner = aliased(LinkUserLecture)
    sole_owned_lecture = select(LinkUserLecture.lecture_id).where(
        LinkUserLecture.user_id == user_id,
        LinkUserLecture.role == LectureRole.OWNER,
        ~exists().where(
            col(other_owner.lecture_id) == LinkUserLecture.lecture_id,
            col(other_owner.user_id) != user_id,
            col(other_owner.role) == LectureRole.OWNER,
        ),
    )

    return session.exec(select(exists(sole_owned_lecture))).one()
