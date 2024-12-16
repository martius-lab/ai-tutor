import reflex as rx

def sidebar_default() -> rx.Component:
    """Render the sidebar component with links, styled to match registration page."""
    return rx.container(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.heading(
                        "AI-Tandempartner",  # Titel in der Sidebar
                        size="4",
                        as_="h4",
                        text_align="center",
                        color="#343a40",
                    ),
                    direction="column",
                    spacing="5",
                    width="100%",
                ),
                # Sidebar Links
                rx.link(
                    "Home",  # Home-Link hinzugefügt
                    href="/",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),  # Blau für Links
                ),
                rx.link(
                    "Login",  # Login-Link hinzugefügt
                    href="/login",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),
                ),
                rx.link(
                    "Registration",  # Registrierungs-Link hinzugefügt
                    href="/register",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),
                ),
                rx.link(
                    "Profile",   # Profil-Link hinzugefügt
                    href="/profile",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),
                ),
                rx.link(
                    "Chat",   # Chat-Link hinzugefügt
                    href="/chat",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),
                ),
                rx.link(
                    "Settings",   # Einstellungen-Link hinzugefügt
                    href="/settings",
                    style=rx.Style(font_size="16px", margin="10px", color="#007bff"),
                ),
                direction="column",  # Links vertikal
                align_items="flex-start",  # Links linksbündig ausgerichtet
                width="100%",
            ),
            max_width="15em",  # Sidebar Breite
            size="4",
            width="100%",
            border_radius="10px",  # Abgerundete Ecken für ein weiches Aussehen
            box_shadow="0px 4px 8px rgba(0, 0, 0, 0.1)",  # Schatten für mehr Tiefe
        ),
        padding="1rem",  # Padding für die Sidebar
        background_color="#f8f9fa",  # Heller Hintergrund
        height="100vh",  # Sidebar soll die ganze Höhe einnehmen
    )
