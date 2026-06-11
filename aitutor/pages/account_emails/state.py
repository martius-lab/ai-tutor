"""State for password reset pages."""

import reflex as rx

import aitutor.routes as routes
from aitutor.account_emails import reset_password, send_password_reset
from aitutor.language_state import BackendTranslations as BT
from aitutor.language_state import language_from_value
from aitutor.mail import EmailConfigurationError, EmailDeliveryError


class ForgotPasswordState(rx.State):
    """State for requesting a password reset link."""

    message: str = ""
    error_message: str = ""

    @rx.event
    def on_load(self):
        """Clear page messages."""
        self.message = ""
        self.error_message = ""

    @rx.event
    def request_password_reset(self, form_data):
        """Send a reset link if the account exists."""
        language = language_from_value(form_data.get("language"))
        identifier = form_data["identifier"].strip()
        self.error_message = ""
        if not identifier:
            self.error_message = BT.enter_username_or_email(language)
            return rx.set_focus("identifier")

        try:
            with rx.session() as session:
                send_password_reset(session, identifier=identifier)
                session.commit()
        except (EmailConfigurationError, EmailDeliveryError, OSError):
            self.error_message = BT.password_reset_email_unavailable(language)
            return

        self.message = BT.password_reset_requested_generic(language)


class ResetPasswordState(rx.State):
    """State for resetting a password from an email link."""

    message: str = ""
    error_message: str = ""

    @rx.event
    def on_load(self):
        """Clear reset form messages."""
        self.message = ""
        self.error_message = ""

    @rx.event
    def reset_password(self, form_data):
        """Reset the password if the token is valid."""
        language = language_from_value(form_data.get("language"))
        new_password = form_data["new_password"]
        confirm_password = form_data["confirm_password"]
        if not new_password:
            self.error_message = BT.enter_new_password(language)
            return rx.set_focus("new_password")
        if new_password != confirm_password:
            self.error_message = BT.passwords_do_not_match(language)
            return rx.set_value("confirm_password", "")

        with rx.session() as session:
            success = reset_password(
                session,
                token=getattr(self, "token", ""),
                new_password=new_password,
            )
            session.commit()

        if not success:
            self.error_message = BT.reset_link_invalid_or_expired(language)
            return

        self.error_message = ""
        self.message = BT.password_changed_login_now(language)
        return rx.redirect(routes.LOGIN)
