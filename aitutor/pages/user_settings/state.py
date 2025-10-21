"""State for the user settings page."""

import reflex as rx
from reflex_local_auth import LocalUser

from aitutor.auth.state import SessionState
from aitutor.language_state import BackendTranslations as BT


class UserSettingsState(SessionState):
    """State for the user settings page."""

    change_password_message: str = ""
    change_password_success: bool = False

    @rx.event
    def reset_change_password_state(self) -> None:
        """Reset the state variables related to changing the password."""
        self.change_password_message = ""
        self.change_password_success = False

    @rx.event
    def handle_change_password(self, form_data):
        """Save the new password."""
        # validate current password
        if not self.authenticated_user.verify(form_data["current_password"]):
            self.change_password_success = False
            self.change_password_message = (
                BT.change_password_message_current_does_not_match(self.language)
            )
            return

        if form_data["new_password"] != form_data["confirm_new_password"]:
            self.change_password_success = False
            self.change_password_message = (
                BT.change_password_message_confirmed_does_not_match(self.language)
            )
            return

        with rx.session() as session:
            local_user = session.get(LocalUser, self.authenticated_user.id)
            if not local_user:
                self.change_password_success = False
                self.change_password_message = "Internal error"
                return

            local_user.password_hash = LocalUser.hash_password(
                form_data["new_password"]
            )
            session.commit()

        self.change_password_success = True
        self.change_password_message = BT.change_password_message_success(self.language)
