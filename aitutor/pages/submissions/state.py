"""The state for the submissions page."""

import reflex as rx

from reflex_local_auth.user import LocalUser
from aitutor.models import ExerciseResult, UserInfo
from sqlmodel import and_, select


class SubmissionsState(rx.State):
    """State for the submissions page."""

    users_with_results: list[tuple[LocalUser, UserInfo, ExerciseResult]] = []

    @rx.event
    def on_load(self):
        """Loads the users and the submissions."""
        with rx.session() as session:
            stmt = (
                select(LocalUser, UserInfo, ExerciseResult)
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
            self.users_with_results = [
                (x[0], x[1], x[2]) for x in session.exec(stmt).all()
            ]

            # Debugging output to check the loaded users and results. TODO: Remove later
            for user_with_result in self.users_with_results:
                print(
                    f"User: {user_with_result[0].username}, "
                    f"user role: {user_with_result[1].role.name}, "
                    f"Result ID: {
                        user_with_result[2].id if user_with_result[2] else 'None'
                    }"
                    "\n"
                )
