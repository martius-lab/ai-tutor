"""State for the manage users page."""

import reflex as rx
from sqlmodel import select

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import LocalUser, UserInfo, UserRole


class ManageUsersState(SessionState):
    """State for managing user accounts."""

    users: list[tuple[LocalUser, UserInfo]] = []
    edited_user: tuple[LocalUser, UserInfo] | None = None
    edit_dialog_is_open: bool = False

    @rx.event
    @state_require_role_at_least(UserRole.ADMIN)
    def on_load(self):
        """Initialize the state"""
        self.global_load()
        self.load_users()

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.users = []

    def load_users(self):
        """Load the users from the database."""
        with rx.session() as session:
            query = select(LocalUser, UserInfo).join(UserInfo)
            self.users = list(session.exec(query).all())

    @rx.event
    def close_edit_dialog(self):
        """Close the edit dialog."""
        self.edit_dialog_is_open = False
        self.edited_user = None

    @rx.event
    def open_edit_dialog(self, user_id: int):
        """Open the edit dialog for a user."""
        user_tuple = next(
            (
                (local_user, user_info)
                for local_user, user_info in self.users
                if local_user.id == user_id
            ),
            None,
        )
        if not user_tuple:
            return rx.toast.error(
                "Fatal error: User not found",
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        self.edited_user = user_tuple
        self.edit_dialog_is_open = True

    @rx.event
    def update_user(self, form_data):
        """Save changes to a user from the edit form."""
        print(form_data)

        self.close_edit_dialog()
