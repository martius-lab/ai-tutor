"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.

This class has all strings used in the frontend code. Strings that are used in the
backend code (e.g. error/success messages) are in the corresponding state class.
"""

import reflex as rx

from aitutor.auth.state import SessionState, LanguageEnum


def backend_translate(language: LanguageEnum, *, de: str, en: str) -> str:
    """Helper function to translate strings in the backend."""
    match language:
        case LanguageEnum.DE:
            return de
        case _:
            return en


class LanguageState(SessionState):
    """State that returns all strings in the current language."""

    def translate(self, *, de: str, en: str) -> str:
        """Helper function to translate strings."""
        match self.language:
            case LanguageEnum.DE:
                return de
            case _:
                return en

    # General Strings ------------------------------------------------------------------
    @rx.var
    def confirm(self) -> str:
        """Confirm string"""
        return self.translate(de="Bestätigen", en="Confirm")

    @rx.var
    def cancel(self) -> str:
        """Cancel string"""
        return self.translate(de="Abbrechen", en="Cancel")

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

    # Exercise Page Strings ------------------------------------------------------------
    @rx.var
    def deadline(self) -> str:
        """Deadline string"""
        return self.translate(de="Frist:", en="Deadline:")

    @rx.var
    def time_left(self) -> str:
        """Time left string"""
        return self.translate(de="Verbleibende Zeit:", en="Time left:")

    @rx.var
    def last_submit(self) -> str:
        """Last submit string"""
        return self.translate(de="Zuletzt abgegeben: ", en="Last submit: ")

    @rx.var
    def deadline_has_passed(self) -> str:
        """Deadline has passed string"""
        return self.translate(de="Frist ist abgelaufen", en="deadline has passed")

    # Chat Page Strings ----------------------------------------------------------------
    @rx.var
    def view_your_submission(self) -> str:
        """View your submission string"""
        return self.translate(
            de="Sehen Sie sich Ihre Abgabe an", en="View your submitted conversation"
        )

    @rx.var
    def reset_conversation(self) -> str:
        """Reset conversation string"""
        return self.translate(de="Chat zurücksetzen", en="Reset chat")

    @rx.var
    def reset_string(self) -> str:
        """Reset string"""
        return self.translate(de="Zurücksetzen", en="Reset")

    @rx.var
    def reset_info_message_submitted(self) -> str:
        """Reset info message string"""
        return self.translate(
            de=(
                "Möchten Sie den Chat wirklich zurücksetzen? "
                + "(Dies löscht Ihre Abgabe nicht.)"
            ),
            en=(
                "Are you sure you want to reset the conversation? "
                + "(This will not delete your submission.)"
            ),
        )

    @rx.var
    def reset_info_message_not_submitted(self) -> str:
        """Reset info message string"""
        return self.translate(
            de="Möchten Sie den Chat wirklich zurücksetzen?",
            en="Are you sure you want to reset the conversation?",
        )

    @rx.var
    def submit(self) -> str:
        """Submit string"""
        return self.translate(de="Abgeben", en="Submit")

    @rx.var
    def check_conversation(self) -> str:
        """Check conversation string"""
        return self.translate(de="Konversation überprüfen", en="Check conversation")

    @rx.var
    def check(self) -> str:
        """Check string"""
        return self.translate(de="Überprüfen", en="Check")

    @rx.var
    def check_conversation_info(self) -> str:
        """Check conversation info string"""
        return self.translate(
            de="Sind Sie mit der Übung fertig und möchten Ihre "
            "Konversation überprüfen?",
            en="Are you done with the exercise and want to check your conversation?",
        )

    @rx.var
    def not_submitted_yet(self) -> str:
        """Not submitted yet string"""
        return self.translate(
            de="Noch nicht abgegeben",
            en="Not submitted yet",
        )

    @rx.var
    def cannot_submit_anymore_info(self) -> str:
        """Cannot submit anymore info string"""
        return self.translate(
            de="Dieser Chat kann nicht mehr abgegeben werden. "
            "Die Frist ist abgelaufen.",
            en="This chat can no longer be submitted. The deadline has passed.",
        )

    @rx.var
    def deadline_has_passed_info(self) -> str:
        """Deadline has passed info string"""
        return self.translate(
            de="Die Frist für diese Übung ist abgelaufen.",
            en="The deadline for this exercise has passed.",
        )

    @rx.var
    def edit_last_message(self) -> str:
        """Edit last message string"""
        return self.translate(
            de="Letzte Nachricht bearbeiten",
            en="Edit last message",
        )

    @rx.var
    def edit_last_message_info(self) -> str:
        """Edit last message info string"""
        return self.translate(
            de="Möchten Sie diese Nachricht löschen und "
            "in das Eingabefeld verschieben?",
            en="Do you want to delete this message and move it to the input field?",
        )

    @rx.var
    def your_answer(self) -> str:
        """Your answer string"""
        return self.translate(
            de="Ihre Antwort",
            en="Your answer",
        )

    # Finished View Page Strings -------------------------------------------------------
    @rx.var
    def delete_submission(self) -> str:
        """Delete submission string"""
        return self.translate(de="Abgabe löschen", en="Delete submission")

    @rx.var
    def delete_submission_info(self) -> str:
        """Delete submission info string"""
        return self.translate(
            de="Möchten Sie Ihre Abgabe wirklich löschen?",
            en="Are you sure you want to delete your submision?",
        )

    @rx.var
    def submitted_chat(self) -> str:
        """submitted chat string"""
        return self.translate(de="Abgegebener Chat für:", en="Submitted chat for:")
