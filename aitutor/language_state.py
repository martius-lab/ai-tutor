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

    # Home Page Strings ----------------------------------------------------------------
    @rx.var
    def dashboard(self) -> str:
        """The string for the 'Dashboard' heading."""
        match self.language:
            case LanguageEnum.DE:
                return "Übersicht"
            case _:
                return "Dashboard"

    @rx.var
    def welcome_back(self) -> str:
        """Welcome back string"""
        username = self.authenticated_user.username
        match self.language:
            case LanguageEnum.DE:
                return f"Willkommen zurück, {username}!"
            case _:
                return f"Welcome back, {username}!"

    @rx.var
    def welcome_message(self) -> str:
        """Welcome message"""
        match self.language:
            case LanguageEnum.DE:
                return (
                    "Willkommen beim AI Tutor. Bitte melden Sie sich an oder "
                    "registrieren Sie sich, um Ihren Fortschritt zu sehen."
                )
            case _:
                return (
                    "Welcome to the AI Tutor. Please log in or register to see "
                    "your progress."
                )

    @rx.var
    def how_to_use_aitutor(self) -> str:
        """How to use AI Tutor string"""
        match self.language:
            case LanguageEnum.DE:
                return "So verwenden Sie den AI Tutor"
            case _:
                return "How To Use AI Tutor"

    @rx.var
    def general_info(self) -> str:
        """General info string"""
        match self.language:
            case LanguageEnum.DE:
                return "Allgemeine Informationen"
            case _:
                return "General Information"

    @rx.var
    def lecture_info(self) -> str:
        """Lecture info string"""
        match self.language:
            case LanguageEnum.DE:
                return "Informationen zur Vorlesung"
            case _:
                return "Lecture Information"

    @rx.var
    def open_exercises_submitted(self) -> str:
        """Open exercises submitted string"""
        match self.language:
            case LanguageEnum.DE:
                return "offene Übungen abgegeben"
            case _:
                return "open exercises submitted"

    @rx.var
    def next_deadline(self) -> str:
        """Next deadline string"""
        match self.language:
            case LanguageEnum.DE:
                return "Nächste Frist:"
            case _:
                return "Next Deadline:"

    @rx.var
    def no_pending_exercises(self) -> str:
        """No pending exercises string"""
        match self.language:
            case LanguageEnum.DE:
                return "Keine ausstehenden Übungen"
            case _:
                return "No pending exercises"

    @rx.var
    def no_upcoming_deadlines(self) -> str:
        """No upcoming deadlines string"""
        match self.language:
            case LanguageEnum.DE:
                return "Keine bevorstehenden Fristen"
            case _:
                return "No upcoming deadlines"
