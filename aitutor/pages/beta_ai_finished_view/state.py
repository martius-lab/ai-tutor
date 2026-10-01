"""State for the student Beta AI finished view."""

import reflex as rx
from sqlmodel import Session, select

from aitutor import routes
from aitutor.auth.protection import state_require_lecture_role
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import BetaExercise, BetaExerciseResult, LectureRole
from aitutor.utilities.lecture_permissions import user_may_view_lecture


def withdraw_beta_submission(beta_result: BetaExerciseResult) -> None:
    """Withdraw only the submitted snapshot while preserving Beta AI progress."""
    beta_result.finished_conversation = []
    beta_result.submit_time_stamp = None


class BetaAIFinishedViewState(SessionState):
    """Student-facing view of a submitted Beta AI conversation."""

    _beta_exercise_id: int
    current_lecture_id: int | None = None
    messages: list[dict[str, str]] = []
    exercise_title: str = ""

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def on_load(self):
        """Load the submitted Beta AI conversation for the current student."""
        self.global_load()
        self.current_lecture_id = None
        self.messages = []
        self.exercise_title = ""
        userinfo = self.authenticated_user_info
        if userinfo is None or userinfo.id is None:
            yield rx.redirect(routes.LOGIN)
            return

        try:
            lecture_id = self.get_route_param_or_error("lecture_id", dtype=int)
            self._beta_exercise_id = self.get_route_param_or_error(
                "beta_exercise_id", dtype=int
            )
        except KeyError, ValueError:
            yield rx.redirect(routes.NOT_FOUND)
            return

        with rx.session() as session:
            result = session.exec(
                select(BetaExercise, BetaExerciseResult.finished_conversation)
                .join(BetaExerciseResult)
                .where(
                    BetaExercise.id == self._beta_exercise_id,
                    BetaExerciseResult.userinfo_id == userinfo.id,
                    BetaExerciseResult.submit_time_stamp != None,
                )
            ).one_or_none()
            if result is None:
                yield rx.redirect(routes.NOT_FOUND)
                return
            exercise, finished_conversation = result
            if exercise.lecture_id != lecture_id:
                yield rx.redirect(routes.NOT_FOUND)
                return
            if not self._user_may_view_exercise(session, exercise):
                yield rx.redirect(routes.MY_LECTURES)
                return
            self.current_lecture_id = exercise.lecture_id
            self.exercise_title = exercise.title
            self.messages = list(finished_conversation)

    @rx.var
    def chat_url(self) -> str:
        """Return the Beta AI chat URL."""
        return (
            f"{routes.BETA_AI_CHAT}/{self.current_lecture_id}/{self._beta_exercise_id}"
        )

    def _user_may_view_exercise(self, session: Session, exercise: BetaExercise) -> bool:
        """Check the same lecture access for viewing and withdrawing a submission."""
        return not (
            exercise.lecture_id is None
            or self.authenticated_user is None
            or self.authenticated_user.id is None
            or not user_may_view_lecture(
                session,
                user_id=self.authenticated_user.id,
                global_permissions=self.global_permissions,
                lecture_id=exercise.lecture_id,
            )
        )

    @rx.event
    @state_require_lecture_role(LectureRole.STUDENT)
    def delete_submission(self):
        """Withdraw the current student's submission without deleting learning state."""
        userinfo = self.authenticated_user_info
        if userinfo is None or userinfo.id is None:
            return rx.redirect(routes.LOGIN)

        with rx.session() as session:
            exercise = session.get(BetaExercise, self._beta_exercise_id)
            if exercise is None or exercise.lecture_id is None:
                return rx.redirect(routes.NOT_FOUND)

            if exercise.lecture_id != self.get_route_param_or_error(
                "lecture_id", dtype=int
            ):
                return rx.redirect(routes.NOT_FOUND)

            if not self._user_may_view_exercise(session, exercise):
                return rx.redirect(routes.MY_LECTURES)

            beta_result = session.exec(
                select(BetaExerciseResult).where(
                    BetaExerciseResult.beta_exercise_id == self._beta_exercise_id,
                    BetaExerciseResult.userinfo_id == userinfo.id,
                    BetaExerciseResult.submit_time_stamp != None,
                )
            ).one_or_none()
            if beta_result is None:
                return rx.redirect(routes.NOT_FOUND)

            withdraw_beta_submission(beta_result)
            session.add(beta_result)
            session.commit()

        return [
            rx.toast.success(
                title=BT.submission_deleted_title(self.language),
                description=BT.submission_deleted_description(self.language),
                duration=2500,
                position="bottom-center",
                invert=True,
            ),
            rx.redirect(self.chat_url),
        ]
