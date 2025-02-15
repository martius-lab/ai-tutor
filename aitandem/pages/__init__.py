from .login import login_default
from .settings import settings_default
from .chat import chat_default
from .profile import profile_default
from .home import home_default
from .registration import registration_default
from .sidebar import sidebar_default  # Füge die Sidebar hier hinzu
from .exercises import exercises_default

__all__ = [
    "login_default",
    "settings_default",
    "chat_default",
    "profile_default",
    "home_default",
    "registration_default",
    "sidebar_default",  # Füge die Sidebar zu __all__ hinzu
    "exercises_default",
]
