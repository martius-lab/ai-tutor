"""State for the email verification page."""

import reflex as rx

import aitutor.routes as routes
from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Language
from aitutor.verification import RedeemResult, redeem_email_token


class VerifyEmailState(rx.State):
    """State for the page that redeems an email verification token."""

    #: Outcome of redeeming the token, i.e. the value of a `RedeemResult`.  Empty for as
    #: long as the token has not been checked yet.
    result: str = ""

    @rx.event
    async def on_load(self):
        """Redeem the token from the query string and report what happened."""
        self.result = ""

        session_state = await self.get_state(SessionState)
        session_state.global_load()

        # The link carries the language of the mail it was sent in.
        try:
            session_state.language = Language(
                self.router.url.query_parameters.get("lang", "en")
            )
        except ValueError:
            pass
        language = session_state.language

        # A missing or empty token simply does not match any stored hash, so it needs
        # no special case here and ends up as RedeemResult.UNKNOWN.
        token = self.router.url.query_parameters.get("token", "")

        with rx.session() as session:
            result = redeem_email_token(session, token)
            session.commit()

        self.result = result.value

        if result in (RedeemResult.SUCCESS, RedeemResult.ALREADY_USED):
            # The address is confirmed, so the only thing left to do is logging in.
            yield rx.toast.success(
                BT.email_verified_successfully(language),
                duration=10_000,
                position="bottom-center",
                invert=True,
            )
            yield rx.redirect(routes.LOGIN)
