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

        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .where(LocalUser.id == user_id)
            )
            self.edited_user = session.exec(query).one_or_none()

        if not self.edited_user:
            return rx.toast.error(
                "Fatal error: User not found",
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        self.edit_dialog_is_open = True

    @rx.event
    def update_user(self, form_data):
        """Save changes to a user from the edit form."""
        print(form_data)
        assert self.edited_user is not None
        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .where(LocalUser.id == self.edited_user[0].id)
            )
            local_user, user_info = session.exec(query).one()

            local_user.username = form_data["username"]
            user_info.email = form_data["email"]
            user_info.role = UserRole[form_data["role"]]

            if form_data["new_password"]:
                local_user.password_hash = LocalUser.hash_password(
                    form_data["new_password"]
                )

            # Reflex devs decided to implement checkboxes in a very smart way.  Instead
            # of having a boolean true/false value, they add it with value "on" in the
            # form_data if it is checked, and do not add it at all if it is not checked.
            local_user.enabled = form_data.get("enabled") == "on"

            session.commit()

        # reload users to update the table
        self.load_users()
        self.close_edit_dialog()
