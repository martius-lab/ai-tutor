import reflex as rx


def home_default() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Welcome to AI Tandem Partner!", size="9"),
            rx.text(
                "Get started by talking to your Tandem Partner! ",
                # rx.code(f"{config.app_name}/{config.app_name}.py"),
                size="5",
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
        rx.logo(),
    )
