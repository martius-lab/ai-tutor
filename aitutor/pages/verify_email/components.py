"""Components for the email verification page."""

import reflex as rx
from reflex_components_radix.themes.base import LiteralAccentColor
from reflex_local_auth.pages.components import MIN_WIDTH

from aitutor import routes
from aitutor.components.dialogs import TextLike
from aitutor.language_state import LanguageState as LS
from aitutor.pages.verify_email.state import VerifyEmailState
from aitutor.verification import RedeemResult


def outcome_callout(
    message: TextLike, *, icon: str, color_scheme: LiteralAccentColor
) -> rx.Component:
    """Render the message describing the outcome of opening a verification link."""
    return rx.callout(
        message,
        icon=icon,
        color_scheme=color_scheme,
        role="alert",
        width="100%",
    )


def verify_email_outcome() -> rx.Component:
    """Render the outcome of redeeming the token, or a spinner while it is checked."""
    return rx.cond(
        VerifyEmailState.result == "",
        rx.center(rx.spinner(size="3"), width="100%"),
        rx.match(
            VerifyEmailState.result,
            (
                RedeemResult.SUCCESS,
                outcome_callout(
                    LS.verify_email_success, icon="check", color_scheme="green"
                ),
            ),
            (
                RedeemResult.ALREADY_USED,
                outcome_callout(
                    LS.verify_email_already_confirmed,
                    icon="check",
                    color_scheme="green",
                ),
            ),
            (
                RedeemResult.EXPIRED,
                outcome_callout(
                    LS.verify_email_expired,
                    icon="triangle_alert",
                    color_scheme="amber",
                ),
            ),
            (
                RedeemResult.ERROR,
                outcome_callout(
                    LS.verify_email_error,
                    icon="triangle_alert",
                    color_scheme="red",
                ),
            ),
            # RedeemResult.UNKNOWN, and anything that might be added later
            outcome_callout(
                LS.verify_email_invalid,
                icon="triangle_alert",
                color_scheme="red",
            ),
        ),
    )


def verify_email_content() -> rx.Component:
    """Render the content of the email verification page."""
    return rx.vstack(
        rx.heading(LS.verify_email_heading, size="7"),
        verify_email_outcome(),
        rx.center(
            rx.link(LS.log_in, href=routes.LOGIN),
            width="100%",
        ),
        min_width=MIN_WIDTH,
        spacing="4",
    )
