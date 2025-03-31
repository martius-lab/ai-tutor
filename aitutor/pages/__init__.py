from .login import login_default
from .chat import chat_default
from .home import home_default
from .registration import registration_default
from .add_excercises import add_exercises_default
from .sidebar import sidebar_default  # Füge die Sidebar hier hinzu
from .exercises import exercises_default

__all__ = [
    "login_default",
    "chat_default",
    "home_default",
    "registration_default",
    "add_exercises_default",
    "sidebar_default",  # Füge die Sidebar zu __all__ hinzu
    "exercises_default",
]
