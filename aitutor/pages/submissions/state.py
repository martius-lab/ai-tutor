"""The state for the submissions page."""

import reflex as rx

from reflex_local_auth.user import LocalUser
from aitutor.models import ExerciseResult, UserInfo, Exercise, UserRole
from sqlmodel import and_, select
from aitutor import routes


class SubmissionsState(rx.State):
    """State for the submissions page."""

    exercise_title: str = ""
    table_rows: list[tuple[str, str, bool]]  # name, role, has_submitted

    @rx.var
    def finished_view_url(self) -> str:
        """
        The exercise_id is used to identify the current exercise.
        It is set by the route parameter in the URL.
        """
        return f"{routes.FINISHED_VIEW}/{self.router.page.params.get('exercise_id', 0)}"

    @rx.event
    def on_load(self):
        """Loads the users and the submissions."""
        with rx.session() as session:
            stmt = (
                select(
                    LocalUser.username,
                    UserInfo.role,
                    ExerciseResult.finished_conversation,
                )
                .join(
                    UserInfo,
                    and_(LocalUser.id == UserInfo.user_id),
                )
                .join(
                    ExerciseResult,
                    and_(
                        LocalUser.id == ExerciseResult.userinfo_id,
                        ExerciseResult.exercise_id == self.exercise_id,
                    ),
                    isouter=True,
                )
            )
            self.table_rows = [
                (
                    x[0],  # name
                    UserRole(x[1]).name,  # userrole
                    x[2] != [] and x[2] is not None,  # -> submission exists
                )
                for x in session.exec(stmt).all()
            ]
            title = session.exec(
                select(Exercise.title).where(Exercise.id == int(self.exercise_id))
            ).one_or_none()
            if title:
                self.exercise_title = title
