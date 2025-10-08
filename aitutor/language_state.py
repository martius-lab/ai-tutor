# ruff: noqa D102
"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.

This class has all strings used in the frontend code. Strings that are used in the
backend code (e.g. error/success messages) are in the corresponding state class.
"""

import reflex as rx

from aitutor.auth.state import SessionState, Language


def translate(language: Language, *, de: str, en: str) -> str:
    """Helper function to translate strings in the backend."""
    match language:
        case Language.DE:
            return de
        case _:
            return en


class LanguageState(SessionState):
    """State that returns all strings in the current language."""

    def translate(self, *, de: str, en: str) -> str:
        """Helper function to translate strings in the LanguageState."""
        return translate(self.language, de=de, en=en)

    # General Strings ------------------------------------------------------------------
    @rx.var
    def confirm(self) -> str:
        """Confirm string"""
        return self.translate(de="Bestätigen", en="Confirm")

    @rx.var
    def cancel(self) -> str:
        """Cancel string"""
        return self.translate(de="Abbrechen", en="Cancel")

    @rx.var
    def log_in(self) -> str:
        """Log in string"""
        return self.translate(de="Anmelden", en="Log in")

    @rx.var
    def register(self) -> str:
        """Register string"""
        return self.translate(de="Registrieren", en="Register")

    @rx.var
    def username(self) -> str:
        """Username string"""
        return self.translate(de="Benutzername", en="Username")

    @rx.var
    def email(self) -> str:
        """Email string"""
        return self.translate(de="E-Mail", en="Email")

    # Search Bar Strings ---------------------------------------------------------------
    @rx.var
    def search_placeholder(self) -> str:
        """Search placeholder string"""
        return self.translate(de="tag:tagname", en="tag:tagname")

    @rx.var
    def search_info_one(self) -> str:
        """Search info string part one"""
        return self.translate(
            de="Suchen Sie mit 'key:Suchbegriff' oder 'key:\"Suchbegriff\"'",
            en="Search with 'key:searchValue' or 'key:\"search value\"' "
            "to search a specific column.",
        )

    @rx.var
    def search_info_two(self) -> str:
        """Search info string part two"""
        return self.translate(
            de="Ohne Verwendung von 'key:' wird in allen Spalten gesucht.",
            en="Without using 'key:' it searches in all columns.",
        )

    # Navigation Bar Strings -----------------------------------------------------------
    @rx.var
    def home_link(self) -> str:
        """The string for the 'Home' link."""
        return self.translate(de="Startseite", en="Home")

    @rx.var
    def exercises_link(self) -> str:
        """The string for the 'Exercises' link."""
        return self.translate(de="Übungen", en="Exercises")

    @rx.var
    def submissions_link(self) -> str:
        """The string for the 'Submissions' link."""
        return self.translate(de="Abgaben", en="Submissions")

    @rx.var
    def manage_exercises_link(self) -> str:
        """The string for the 'Manage Exercises' link."""
        return self.translate(de="Übungsverwaltung", en="Manage Exercises")

    @rx.var
    def language_string(self) -> str:
        """The current language as a string."""
        return self.translate(de="Deutsch", en="English")

    @rx.var
    def log_out(self) -> str:
        """Log out string"""
        return self.translate(de="Abmelden", en="Log out")

    # Home Page Strings ----------------------------------------------------------------
    @rx.var
    def dashboard(self) -> str:
        """The string for the 'Dashboard' heading."""
        return self.translate(de="Übersicht", en="Dashboard")

    @rx.var(initial_value="")
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
            de="offenen Übungen abgegeben", en="open exercises submitted"
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

    @rx.var
    def impressum(self) -> str:
        """Impressum string"""
        return self.translate(de="Impressum", en="Impressum")

    @rx.var
    def privacy_notice(self) -> str:
        """Datenschutzerklärung string"""
        return self.translate(de="Datenschutzerklärung", en="Privacy Notice")

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

    @rx.var
    def open_deadline(self) -> str:
        """Open deadline string"""
        return self.translate(de="Offene Frist", en="Open Deadline")

    @rx.var
    def no_deadline(self) -> str:
        """No deadline string"""
        return self.translate(de="Keine Frist", en="No Deadline")

    @rx.var
    def closed_deadline(self) -> str:
        """Closed deadline string"""
        return self.translate(de="Frist abgelaufen", en="Closed Deadline")

    @rx.var
    def no_exercises_available(self) -> str:
        """No exercises available string"""
        return self.translate(
            de="Keine Übungen verfügbar",
            en="No exercises available",
        )

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
        return self.translate(de="Abgegebener Chat für:", en="Submitted chat for:")  #

    @rx.var
    def user(self) -> str:
        """User string"""
        return self.translate(de="Benutzer", en="User")

    @rx.var
    def exercise(self) -> str:
        """Exercise string"""
        return self.translate(de="Übung", en="Exercise")

    @rx.var
    def tags(self) -> str:
        """Tags string"""
        return self.translate(de="Tags", en="Tags")

    @rx.var
    def submission(self) -> str:
        """Submission string"""
        return self.translate(de="Abgabe", en="Submission")

    @rx.var
    def only_with_submission(self) -> str:
        """Only with submission string"""
        return self.translate(
            de="Nur mit Abgabe",
            en="Only with submission",
        )

    @rx.var
    def no_submission(self) -> str:
        """No submission string"""
        return self.translate(
            de="Keine Abgabe",
            en="No submission",
        )

    # Finished View Teacher Page Strings -----------------------------------------------
    @rx.var
    def submitted_chat_teacher(self) -> str:
        """Submitted chat string"""
        return self.translate(de="Abgegebener Chat", en="Submitted chat")

    # Manage Exercises Page Strings ----------------------------------------------------
    @rx.var
    def new_tag(self) -> str:
        """Create new tag string"""
        return self.translate(de="Neues Tag", en="New tag")

    @rx.var
    def tagname(self) -> str:
        """Name string"""
        return self.translate(de="Tag Name", en="tagname")

    @rx.var
    def add_tag(self) -> str:
        """Add tag string"""
        return self.translate(de="Tag hinzufügen", en="Add tag")

    @rx.var
    def delete_exercise(self) -> str:
        """Delete exercise string"""
        return self.translate(de="Übung löschen", en="Delete exercise")

    @rx.var
    def delete_exercise_info(self) -> str:
        """Delete exercise info string"""
        return self.translate(
            de="Möchten Sie diese Übung wirklich löschen?",
            en="Are you sure you want to delete this exercise?",
        )

    @rx.var
    def exercise_hidden_hover_info(self) -> str:
        """Exercise hidden hover info string"""
        return self.translate(
            de="Übung wird bis zum Veröffentlichungsdatum automatisch ausgeblendet.",
            en="Exercise is automatically hidden until its release date.",
        )

    @rx.var
    def description(self) -> str:
        """Description string"""
        return self.translate(de="Beschreibung", en="Description")

    @rx.var
    def editing_period(self) -> str:
        """Editing period string"""
        return self.translate(de="Bearbeitungszeitraum", en="Editing period")

    @rx.var
    def settings(self) -> str:
        """Settings string"""
        return self.translate(de="Einstellungen", en="Settings")

    @rx.var
    def add_exercise(self) -> str:
        """Add exercise string"""
        return self.translate(de="Neue Übung", en="Add exercise")

    @rx.var
    def add_exercise_description(self) -> str:
        """Add exercise description string"""
        return self.translate(
            de="Fügen Sie eine neue Übung für die Studenten hinzu",
            en="add a new exercise for the students",
        )

    @rx.var
    def edit_exercise(self) -> str:
        """Edit exercise string"""
        return self.translate(de="Übung bearbeiten", en="Edit exercise")

    @rx.var
    def edit_exercise_description(self) -> str:
        """Edit exercise description string"""
        return self.translate(
            de="Bereits vorhandene Übung bearbeiten",
            en="Edit already existing exercise",
        )

    @rx.var
    def add_lesson_context_pdf(self) -> str:
        """Add lesson context pdf string"""
        return self.translate(
            de="Aufgabenkontext (PDF) hinzufügen:",
            en="Add lesson context (PDF):",
        )

    @rx.var
    def select_file(self) -> str:
        """Select file string"""
        return self.translate(de="Datei auswählen", en="Select file")

    @rx.var
    def pdf_upload_info(self) -> str:
        """PDF upload info string"""
        return self.translate(
            de="Drag & Drop oder auf den Button klicken, um auszuwählen",
            en="Drag and drop or click the button to select",
        )

    @rx.var
    def last_uploaded_file(self) -> str:
        """Last uploaded file string"""
        return self.translate(
            de="Zuletzt hochgeladene Datei:",
            en="Last uploaded file:",
        )

    @rx.var
    def prompt(self) -> str:
        """Prompt string"""
        return self.translate(de="Prompt:", en="Prompt:")

    @rx.var
    def select_prompt(self) -> str:
        """Select prompt string"""
        return self.translate(de="Prompt auswählen", en="Select prompt")

    @rx.var
    def select_tag(self) -> str:
        """Select tag string"""
        return self.translate(de="Tag auswählen", en="Select tag")

    @rx.var
    def link_tag_to_exercise(self) -> str:
        """Link tag to exercise string"""
        return self.translate(de="Tag mit Übung verknüpfen", en="Link tag to exercise")

    @rx.var
    def title(self) -> str:
        """Title string"""
        return self.translate(de="Titel:", en="Title:")

    @rx.var
    def exercise_title_placeholder(self) -> str:
        """Exercise title placeholder string"""
        return self.translate(
            de="Titel der Übung",
            en="Exercise title",
        )

    @rx.var
    def description_placeholder(self) -> str:
        """Description placeholder string"""
        return self.translate(
            de="Beschreibung der Übung. Dies ist die erste Nachricht, "
            "die der Student im Chat sieht.",
            en="Describe the task here. This is the first message "
            "the student sees in the chat.",
        )

    @rx.var
    def lesson_context(self) -> str:
        """Lesson context string"""
        return self.translate(de="Aufgabenkontext:", en="Lesson context:")

    @rx.var
    def lesson_context_placeholder(self) -> str:
        """Lesson context placeholder string"""
        return self.translate(
            de="Fügen Sie hier den Aufgabenkontext hinzu. Der Kontext hilft der KI zu "
            "beurteilen, ob die Antwort des Studenten ausreichend ist.",
            en="Add lesson context here. The context helps the AI to assess whether "
            "the student's answer is sufficient.",
        )

    @rx.var
    def hide_exercise(self) -> str:
        """Hide exercises string"""
        return self.translate(de="Übung ausblenden:", en="Hide exercise:")

    @rx.var
    def activate_deadline(self) -> str:
        """Activate deadline string"""
        return self.translate(de="Frist aktivieren:", en="Activate deadline:")

    @rx.var
    def days_to_complete(self) -> str:
        """Days to complete string"""
        return self.translate(de="Tage zur Bearbeitung:", en="Days to complete:")

    @rx.var
    def timezone(self) -> str:
        """Timezone string"""
        return self.translate(de="Zeitzone: ", en="Timezone: ")

    @rx.var
    def add_task(self) -> str:
        """Add task string"""
        return self.translate(de="Aufgabe hinzufügen", en="Add exercise")

    @rx.var
    def update_task(self) -> str:
        """Update task string"""
        return self.translate(de="Änderungen speichern", en="Update exercise")

    # Login and Registration Page Strings ----------------------------------------------
    @rx.var
    def login_heading(self) -> str:
        """Login heading string"""
        return self.translate(
            de="Melden Sie sich in Ihrem Konto an", en="Log in to your Account"
        )

    @rx.var
    def password(self) -> str:
        """Password string"""
        return self.translate(de="Passwort", en="Password")

    @rx.var
    def register_heading(self) -> str:
        """Register heading string"""
        return self.translate(de="Erstellen Sie ein Konto", en="Create an account")

    @rx.var
    def confirm_password(self) -> str:
        """Confirm password string"""
        return self.translate(de="Passwort bestätigen", en="Confirm Password")

    @rx.var
    def successful_registration(self) -> str:
        """Successful registration string"""
        return self.translate(
            de="Registrierung erfolgreich! Sie können sich jetzt anmelden.",
            en="Registration successful! You can now log in.",
        )

    @rx.var
    def registration_code(self) -> str:
        """Registration Code string"""
        return self.translate(de="Registrierungscode", en="Registration code")

    @rx.var
    def registration_code_placeholder(self) -> str:
        """Registration code placeholder string"""
        return self.translate(
            de="Sie bekommen diesen Code von Ihrem Lehrer",
            en="You get this code from your teacher",
        )

    # Manage Users Page Strings --------------------------------------------------------
    @rx.var
    def manage_users(self) -> str:
        return self.translate(de="Benutzerverwaltung", en="Manage Users")

    @rx.var
    def edit_user(self) -> str:
        return self.translate(de="Benutzer bearbeiten", en="Edit User")

    @rx.var
    def id(self) -> str:
        return self.translate(de="ID", en="ID")

    @rx.var
    def role(self) -> str:
        return self.translate(de="Rolle", en="Role")

    @rx.var
    def enabled(self) -> str:
        return self.translate(de="Aktiviert", en="Enabled")

    @rx.var
    def new_password(self) -> str:
        return self.translate(de="Neues Passwort", en="New Password")

    @rx.var
    def new_password_placeholder(self) -> str:
        return self.translate(
            de="Leer lassen, um Passwort nicht zu ändern.",
            en="Leave empty to keep current password",
        )

    @rx.var
    def save(self) -> str:
        return self.translate(de="Speichern", en="Save")

    @rx.var
    def edit(self) -> str:
        return self.translate(de="Bearbeiten", en="Edit")

    @rx.var
    def delete(self) -> str:
        return self.translate(de="Löschen", en="Delete")

    @rx.var
    def delete_user(self) -> str:
        return self.translate(de="Benutzer löschen:", en="Delete user:")

    @rx.var
    def delete_user_description(self) -> str:
        return self.translate(
            de="Alle Übungen und Abgaben dieses Benutzers werden ebenfalls gelöscht. Dies kann nicht rückgängig gemacht werden!",
            en="All exercises and submissions of this user will also be deleted.  This cannot be undone!",
        )


class BackendTranslations:
    """Translations for use in the backend (where LanguageState is not available)."""

    # ManageUsersState -----------------------------------------------------------------
    @staticmethod
    def error_user_not_found(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Benutzer existiert nicht.",
            en="Error: User not found",
        )

    @staticmethod
    def deleted_user(language: Language, username: str) -> str:
        return translate(
            language,
            de=f"Benutzer '{username}' wurde gelöscht.",
            en=f"User '{username}' has been deleted.",
        )

    # ManageExercisesState -------------------------------------------------------------
    @staticmethod
    def exercise_added(language: Language) -> str:
        return translate(
            language,
            de="Übung erfolgreich hinzugefügt",
            en="Exercise added successfully",
        )

    @staticmethod
    def tag_was_added(language: Language) -> str:
        return translate(
            language,
            de="Tag wurde hinzugefügt und kann jetzt ausgewählt werden.",
            en="Tag has been added and can now be selected.",
        )

    @staticmethod
    def changes_saved(language: Language) -> str:
        return translate(
            language,
            de="Änderungen erfolgreich gespeichert.",
            en="Exercise updated successfully.",
        )

    @staticmethod
    def tag_deleted(language: Language) -> str:
        return translate(
            language,
            de="Tag erfolgreich gelöscht",
            en="Tag deleted successfully",
        )

    @staticmethod
    def exercise_deleted(language: Language) -> str:
        return translate(
            language,
            de="Übung erfolgreich gelöscht",
            en="Exercise deleted successfully",
        )

    # FinishedViewState ----------------------------------------------------------------
    @staticmethod
    def submission_deleted_title(language: Language) -> str:
        return translate(language, de="Abgabe gelöscht", en="Submission Deleted")

    @staticmethod
    def submission_deleted_description(language: Language) -> str:
        return translate(
            language,
            de="Ihre Abgabe wurde erfolgreich gelöscht.",
            en="Your submission has been deleted successfully.",
        )

    # ChatState ------------------------------------------------------------------------
    @staticmethod
    def successful_submit_title(language: Language) -> str:
        return translate(language, de="Abgabe", en="Submit")

    @staticmethod
    def successful_submit_description(language: Language) -> str:
        return translate(
            language,
            de="Die Aufgabe wurde erfolgreich abgegeben.",
            en="The exercise was submitted successfully.",
        )
