"""Login page, authentication logic,
assign roles when logging in and protected pages."""

import reflex as rx
from aitandem.components.user_roles import get_user_role
from aitandem.components.error_box import error_popup
from ..base_state import State
from ..models import User
from sqlalchemy import select

LOGIN_ROUTE = "/login"
REGISTER_ROUTE = "/register"


class LoginState(State):
    """Handle login form and redirect afterwards."""

    redirect_to: str = ""

    def on_submit(self, form_data) -> rx.event.EventSpec:
        """Handle login form on_submit.

        Args:
            form_data: A dict of form fields and values.
        """
        email = form_data["email"]
        password = form_data["password"]

        # fetch user
        with rx.session() as session:
            user = (
                session.exec(select(User).where(User.email == email))
                .scalars()
                .one_or_none()
            )

        # error message for users with enabled != 1
        if user is not None and not user.enabled:
            return rx.toast.error(
                "This account has been disabled.",
                duration=3500,
                position="bottom-center",
                invert=True,
            )

        # error message for non-existing users /wrong E-Mail/password
        if user is None or password is None or not user.verify(password):
            return rx.toast.error(
                "E-Mail not found or password incorrect.",
                duration=3500,
                position="bottom-center",
                invert=True,
            )

        # successful login
        if (
            user is not None
            and user.id is not None
            and user.enabled
            and user.verify(password)
        ):
            # mark user as logged in and redirect
            self._login(user.id)
        return LoginState.redir()  # type: ignore

    def redir(self) -> rx.event.EventSpec | None:
        """Redirect to home if logged in, or to the login page if not."""
        if not self.is_hydrated:
            # wait until after hydration to ensure auth_token is known
            return LoginState.redir()  # type: ignore

        page = self.router.page.path

        if not self.is_authenticated and page != LOGIN_ROUTE:
            self.redirect_to = page
            return rx.redirect(LOGIN_ROUTE)

        elif page == LOGIN_ROUTE:
            return rx.redirect("/")

        else:
            return None


def handle_student_login(session_id: str) -> rx.Component:
    """students dashboard"""
    return rx.redirect("/student_dashboard")


def handle_teacher_login(session_id: str) -> rx.Component:
    """teachers dashboard"""
    return rx.redirect("/teacher_dashboard")


@rx.page(route=LOGIN_ROUTE)
def login_default() -> rx.Component:
    """Render the login page.

    Returns:
        A reflex component.
    """

    def handle_login(session_id: str) -> rx.Component:
        user_role = get_user_role(session_id)
        if user_role == "student":
            return handle_student_login(session_id)
        elif user_role == "teacher":
            return handle_teacher_login(session_id)
        else:
            error_popup("Unknown role!")

    login_form = rx.form(
        rx.center(
            rx.color_mode.button(position="top-right", type="button"),
            rx.card(
                rx.vstack(
                    rx.center(
                        rx.heading(
                            "Sign in to your account",
                            size="6",
                            as_="h2",
                            text_align="center",
                            width="100%",
                        ),
                        direction="column",
                        spacing="5",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "E-Mail address",
                            size="3",
                            weight="medium",
                            text_align="left",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("user")),
                            placeholder="AI-Tandempartner@example.com",
                            id="email",
                            size="3",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Password",
                            size="3",
                            weight="medium",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("lock")),
                            placeholder="Enter your password",
                            id="password",
                            size="3",
                            width="100%",
                            type="password",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.button("Sign in", type="submit", size="3", width="100%"),
                    rx.center(
                        rx.text("Don't have an account yet?", size="3"),
                        rx.link("Sign up", href=REGISTER_ROUTE, size="3"),
                        opacity="0.8",
                        spacing="2",
                        direction="row",
                        width="100%",
                    ),
                    spacing="6",
                    width="100%",
                ),
                max_width="28em",
                size="4",
                width="100%",
            ),
            height="85vh",
        ),
        # submit form
        on_submit=LoginState.on_submit,
    )
    return rx.fragment(
        rx.cond(
            LoginState.is_hydrated,  # type: ignore
            rx.box(
                login_form,
                height="100vh",
                align="center",
            ),
        ),
    )


def require_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Decorator to require authentication before rendering a protected page.

    If the user is not authenticated, he will be redirected to the login page.

    Args:
        page: The page to wrap.

    Returns:
        The wrapped page component.
    """

    def protected_page():
        return rx.fragment(
            rx.cond(
                State.is_hydrated & State.is_authenticated,  # type: ignore
                page(),
                rx.center(
                    # if user is not authenticated, he will be redirected
                    rx.spinner(on_mount=LoginState.redir),
                ),
            )
        )

    protected_page.__name__ = page.__name__
    return protected_page
