import reflex as rx
from ..components.sidebar import sidebar_default

def home_page_default() -> rx.Component:
    return rx.hstack(
        sidebar_default(),
        rx.container(
            rx.color_mode.button(position="top-right"),
            rx.vstack(
                rx.heading("Welcome to AI Tandem Partner!", size="9"),
                rx.text(
                    "Get started by talking to your Tandem Partner! ",
                    #rx.code(f"{config.app_name}/{config.app_name}.py"),
                    size="5",
                ),
                rx.link(
                    rx.button("Check out our docs!"),
                    href="https://reflex.dev/docs/getting-started/introduction/",
                    is_external=True,
                ),
                spacing="5",
                justify="center",
                min_height="85vh",
            ),
            rx.logo(),
        )
    )