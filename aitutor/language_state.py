"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.
"""

import reflex as rx

from enum import Enum


class LanguageEnum(Enum):
    """Enum for supported languages."""

    EN = "English"
    DE = "Deutsch"


class LanguageState(rx.State):
    """State that returns all strings in the current language."""

    language: LanguageEnum = LanguageEnum.EN

    @rx.event
    def toggle_language(self):
        """Toggle the language between English and German."""
        match self.language:
            case LanguageEnum.EN:
                self.language = LanguageEnum.DE
            case LanguageEnum.DE:
                self.language = LanguageEnum.EN

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
