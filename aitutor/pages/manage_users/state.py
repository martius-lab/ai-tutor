"""State for the manage users page."""

import reflex as rx
from sqlmodel import select
from reflex_local_auth.auth_session import LocalAuthSession
from sqlmodel import case, cast

from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.models import LocalUser, UserInfo, UserRole
from aitutor.language_state import BackendTranslations as BT


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
        self.edited_user = None
        self.edit_dialog_is_open = False

    def load_users(self):
        """Load the users from the database."""
        # Define role order for sorting (based on definition order in the database enum,
        # which hopefully always matches that of UserRole).
        # Based on https://stackoverflow.com/a/23618085/2095383
        role_order_whens = {
            cast(role.name, UserInfo.role.type): role.value  # type: ignore
            for role in UserRole
        }
        role_sort_logic = case(role_order_whens, value=UserInfo.role)

        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .order_by(role_sort_logic.desc(), LocalUser.username)
            )
            self.users = [(lu, ui) for lu, ui in session.exec(query).all()]

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
            row = session.exec(query).one_or_none()

        if not row:
            return rx.toast.error(
                BT.error_user_not_found(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )

        # need to convert to proper tuple to avoid some weird type errors...
        self.edited_user = (row[0], row[1])
        self.edit_dialog_is_open = True

    @rx.event
    def update_user(self, form_data):
        """Save changes to a user from the edit form."""
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

            # if user gets disabled, also end any open sessions they may still have
            if not local_user.enabled:
                user_sessions = session.exec(
                    select(LocalAuthSession).where(
                        LocalAuthSession.user_id == local_user.id
                    )
                ).all()
                for us in user_sessions:
                    session.delete(us)

            session.commit()

        # reload users to update the table
        self.load_users()
        self.close_edit_dialog()

    @rx.event
    def delete_user(self, user_id: int):
        """Delete a user from the database."""
        with rx.session() as session:
            query = (
                select(LocalUser, UserInfo)
                .join(UserInfo)
                .where(LocalUser.id == user_id)
            )
            row = session.exec(query).one_or_none()

            if row:
                local_user, user_info = row

                # NOTE: The deletions below could be reduced to a single delete of
                # LocalUser if delete cascades where set up properly.  However, since
                # LocalUser and LocalAuthSession are defined in the reflex_local_auth,
                # we don't have direct influence on it.

                session.delete(local_user)
                # delete does not cascade from LocalUser to UserInfo, so we need to do
                # this explicilty
                session.delete(user_info)

                # and also delete any open sessions the user may still have (doesn't
                # cascade either...)
                user_sessions = session.exec(
                    select(LocalAuthSession).where(
                        LocalAuthSession.user_id == local_user.id
                    )
                ).all()
                for us in user_sessions:
                    session.delete(us)

                session.commit()
            else:
                return rx.toast.error(
                    BT.error_user_not_found(self.language),
                    duration=5000,
                    position="bottom-center",
                    invert=True,
                )

        # reload the table
        self.load_users()

        return rx.toast.success(
            BT.deleted_user(self.language, local_user.username),
            duration=5000,
            position="bottom-center",
            invert=True,
        )
