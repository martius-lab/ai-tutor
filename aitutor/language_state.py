"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.
"""

import reflex as rx

from aitutor.auth.state import SessionState, LanguageEnum


class LanguageState(SessionState):
    """State that returns all strings in the current language."""

    def translate(self, *, de: str, en: str) -> str:
        """Helper function to translate strings."""
        match self.language:
            case LanguageEnum.DE:
                return de
            case _:
                return en

    # Navigation Bar Strings -----------------------------------------------------------
    @rx.var
    def homeLink(self) -> str:
        """The string for the 'Home' link."""
        return self.translate(de="Startseite", en="Home")

    @rx.var
    def exercisesLink(self) -> str:
        """The string for the 'Exercises' link."""
        return self.translate(de="Übungen", en="Exercises")

    @rx.var
    def SubmissionsLink(self) -> str:
        """The string for the 'Submissions' link."""
        return self.translate(de="Abgaben", en="Submissions")

    @rx.var
    def manageExercisesLink(self) -> str:
        """The string for the 'Manage Exercises' link."""
        return self.translate(de="Übungsverwaltung", en="Manage Exercises")

    @rx.var
    def log_in(self) -> str:
        """Log in string"""
        return self.translate(de="Anmelden", en="Log in")

    @rx.var
    def register(self) -> str:
        """Register string"""
        return self.translate(de="Registrieren", en="Register")

    @rx.var
    def log_out(self) -> str:
        """Log out string"""
        return self.translate(de="Abmelden", en="Log out")

    # Home Page Strings ----------------------------------------------------------------
    @rx.var
    def dashboard(self) -> str:
        """The string for the 'Dashboard' heading."""
        return self.translate(de="Übersicht", en="Dashboard")

    @rx.var
    def welcome_back(self) -> str:
        """Welcome back string"""
        username = self.authenticated_user.username
        return self.translate(
            de=f"Willkommen zurück, {username}!", en=f"Welcome back, {username}!"
        )

    @rx.var
    def welcome_message(self) -> str:
        """Welcome message"""
        return self.translate(
            de=(
                "Willkommen beim AI Tutor. Bitte melden Sie sich an oder "
                "registrieren Sie sich, um Ihren Fortschritt zu sehen."
            ),
            en=(
                "Welcome to the AI Tutor. Please log in or register to see "
                "your progress."
            ),
        )

    @rx.var
    def how_to_use_aitutor(self) -> str:
        """How to use AI Tutor string"""
        return self.translate(
            de="So verwenden Sie den AI Tutor", en="How To Use AI Tutor"
        )

    @rx.var
    def general_info(self) -> str:
        """General info string"""
        return self.translate(de="Allgemeine Informationen", en="General Information")

    @rx.var
    def lecture_info(self) -> str:
        """Lecture info string"""
        return self.translate(
            de="Informationen zur Vorlesung", en="Lecture Information"
        )

    @rx.var
    def open_exercises_submitted(self) -> str:
        """Open exercises submitted string"""
        return self.translate(
            de="offene Übungen abgegeben", en="open exercises submitted"
        )

    @rx.var
    def next_deadline(self) -> str:
        """Next deadline string"""
        return self.translate(de="Nächste Frist:", en="Next Deadline:")

    @rx.var
    def no_pending_exercises(self) -> str:
        """No pending exercises string"""
        return self.translate(
            de="Keine ausstehenden Übungen", en="No pending exercises"
        )

    @rx.var
    def no_upcoming_deadlines(self) -> str:
        """No upcoming deadlines string"""
        return self.translate(
            de="Keine bevorstehenden Fristen", en="No upcoming deadlines"
        )
