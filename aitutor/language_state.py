"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.
"""

import reflex as rx

from aitutor.auth.state import SessionState, LanguageEnum


class LanguageState(SessionState):
    """State that returns all strings in the current language."""

    # Navigation Bar Strings -----------------------------------------------------------
    @rx.var
    def homeLink(self) -> str:
        """The string for the 'Home' link."""
        match self.language:
            case LanguageEnum.DE:
                return "Startseite"
            case _:
                return "Home"

    @rx.var
    def exercisesLink(self) -> str:
        """The string for the 'Exercises' link."""
        match self.language:
            case LanguageEnum.DE:
                return "Übungen"
            case _:
                return "Exercises"

    @rx.var
    def SubmissionsLink(self) -> str:
        """The string for the 'Submissions' link."""
        match self.language:
            case LanguageEnum.DE:
                return "Abgaben"
            case _:
                return "Submissions"

    @rx.var
    def manageExercisesLink(self) -> str:
        """The string for the 'Manage Exercises' link."""
        match self.language:
            case LanguageEnum.DE:
                return "Übungsverwaltung"
            case _:
                return "Manage Exercises"

    @rx.var
    def log_in(self) -> str:
        """Log in string"""
        match self.language:
            case LanguageEnum.DE:
                return "Anmelden"
            case _:
                return "Log in"

    @rx.var
    def register(self) -> str:
        """Register string"""
        match self.language:
            case LanguageEnum.DE:
                return "Registrieren"
            case _:
                return "Register"

    @rx.var
    def log_out(self) -> str:
        """Log out string"""
        match self.language:
            case LanguageEnum.DE:
                return "Abmelden"
            case _:
                return "Log out"
