# ruff: noqa D102
"""
State that returns all strings in the current language.
Every var function checks for the current language and returns the appropriate string.
The base case is English.

This class has all strings used in the frontend code. Strings that are used in the
backend code (e.g. error/success messages) are in the corresponding state class.
"""

import textwrap

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

    @rx.var
    def settings(self) -> str:
        """Settings string"""
        return self.translate(de="Einstellungen", en="Settings")

    @rx.var
    def delete(self) -> str:
        """Delete string"""
        return self.translate(de="Löschen", en="Delete")

    @rx.var
    def prompt(self) -> str:
        return self.translate(
            de="Prompt",
            en="Prompt",
        )

    # Search Bar Strings ---------------------------------------------------------------
    @rx.var
    def search_placeholder(self) -> str:
        """Search placeholder string"""
        return self.translate(de="Suche...", en="Search...")

    @rx.var
    def search_info(self) -> str:
        return self.translate(
            de='Suchen Sie mit `key:Suchbegriff` oder `key:"Such Begriff"`, '
            "um nach etwas Bestimmtem zu suchen.  \n"
            "Ohne Verwendung von `key:` werden alle keys durchsucht.",
            en='Search with `key:searchterm` or `key:"search term"` '
            "to search for something specific.  \n"
            "Without using `key:` every key will be searched.",
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
    def admin_settings_link(self) -> str:
        return self.translate(de="Admin Einstellungen", en="Admin Settings")

    @rx.var
    def lectures_link(self) -> str:
        """The string for the 'Lectures' link."""
        return self.translate(de="Vorlesungen", en="Lectures")

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

    @rx.var
    def privacy_notice_short(self) -> str:
        """Short Datenschutzerklärung string"""
        return self.translate(
            de="Datenschutzerklärung Kurzfassung",
            en="Privacy Notice Summary",
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

    @rx.var
    def show_submitted_exercises(self) -> str:
        return self.translate(
            de="Abgegebene Übungen anzeigen",
            en="Show submitted exercises",
        )

    @rx.var
    def show_closed_exercises(self) -> str:
        return self.translate(
            de="Abgelaufene Übungen anzeigen",
            en="Show closed exercises",
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
    def cannot_submit_anymore_info_mobile(self) -> str:
        """Cannot submit anymore info string for mobile"""
        return self.translate(
            de="Die Frist ist abgelaufen.",
            en="Deadline passed.",
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

    @rx.var
    def token_limit_message(self) -> str:
        return self.translate(
            de="Die maximale Anzahl an Tokens für diese Übung wurde erreicht. Sie können keine weiteren Nachrichten senden oder Überprüfungen durchführen.",
            en="Your token limit has been reached for this exercise. You cannot send more messages or run checks.",
        )

    @rx.var
    def token_warning_message(self) -> str:
        return self.translate(
            de="Token-Nutzungswarnung: Ihre aktuelle Token-Nutzung für diese Übung beträgt ",
            en="Token usage warning: Your current token usage for this exercise is ",
        )

    @rx.var
    def token_warning_message_mobile(self) -> str:
        return self.translate(
            de="Token-Nutzungswarnung: ",
            en="Token usage warning: ",
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
    def no_submission(self) -> str:
        """No submission string"""
        return self.translate(
            de="Keine Abgabe",
            en="No submission",
        )

    @rx.var
    def submission(self) -> str:
        """Submission string"""
        return self.translate(de="Abgabe", en="Submission")

    # Submission Page Strings --------------------------------------------------------
    @rx.var
    def token_limit_reached(self) -> str:
        """Submission string"""
        return self.translate(de="Token-Limit erreicht", en="Token limit reached")

    # Finished View Tutor Page Strings -----------------------------------------------
    @rx.var
    def submitted_chat_tutor(self) -> str:
        """Submitted chat string"""
        return self.translate(de="Abgegebener Chat", en="Submitted chat")

    # Manage Exercises Page Strings ----------------------------------------------------
    @rx.var
    def exercise_count_info(self) -> str:
        return self.translate(
            de="Anzahl der Übungen mit diesem Tag",
            en="Number of exercises with this tag",
        )

    @rx.var
    def delete_tag(self) -> str:
        return self.translate(de="Tag löschen", en="Delete tag")

    @rx.var
    def delete_tag_info(self) -> str:
        return self.translate(
            de="Möchten Sie dieses Tag wirklich löschen? "
            "Das Tag wird von allen Übungen entfernt.",
            en="Are you sure you want to delete this tag? "
            "The tag will be removed from all exercises.",
        )

    @rx.var
    def rename_tag(self) -> str:
        return self.translate(de="Tag umbenennen", en="Rename tag")

    @rx.var
    def edit_tags(self) -> str:
        return self.translate(de="Tags bearbeiten", en="Edit Tags")

    @rx.var
    def import_exercises(self) -> str:
        return self.translate(de="Übungen importieren", en="Import Exercises")

    @rx.var
    def import_(self) -> str:
        return self.translate(de="Importieren", en="Import")

    @rx.var
    def exercises_upload_info(self) -> str:
        return self.translate(
            de="Drag & Drop oder klicken, um aus dem Dateisystem auszuwählen "
            "(JSON-Format erwartet).",
            en="Drag and drop or click to select from file system "
            "(JSON format expected).",
        )

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
            de="Möchten Sie diese Übung wirklich löschen? "
            "Alle Abgaben für diese Übung werden auch gelöscht. "
            "Das kann nicht rückgängig gemacht werden.",
            en="Are you sure you want to delete this exercise? "
            "All submissions for this exercise will be deleted too. "
            "This cannot be undone.",
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
    def add_exercise(self) -> str:
        """Add exercise string"""
        return self.translate(de="Übung Hinzufügen", en="Add Exercise")

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
    def select_prompt(self) -> str:
        """Select prompt string"""
        return self.translate(de="Prompt auswählen", en="Select prompt")

    @rx.var
    def select_tags(self) -> str:
        return self.translate(de="Tags auswählen", en="Select tags")

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
    def add(self) -> str:
        return self.translate(de="Hinzufügen", en="Add")

    @rx.var
    def update_task(self) -> str:
        """Update task string"""
        return self.translate(de="Änderungen speichern", en="Update exercise")

    @rx.var
    def delete_selected_info(self) -> str:
        """Confirmation message for 'delete selected'"""
        return self.translate(
            de="Sind sie sicher, dass sie alle markierten Aufgaben löschen wollen? "
            "Alle Abgaben für diese Aufgaben werden auch gelöscht. "
            "Das kann nicht rückgängig gemacht werden.",
            en="Are you sure you want to delete all selected exercises? "
            "All submissions for these exercises will be deleted too. "
            "This cannot be undone.",
        )

    @rx.var
    def export(self) -> str:
        return self.translate(de="Exportieren", en="Export")

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
    def delete_user(self) -> str:
        return self.translate(de="Benutzer löschen:", en="Delete user:")

    @rx.var
    def delete_user_description(self) -> str:
        return self.translate(
            de="Alle Übungen und Abgaben dieses Benutzers werden ebenfalls gelöscht. Dies kann nicht rückgängig gemacht werden!",
            en="All exercises and submissions of this user will also be deleted.  This cannot be undone!",
        )

    @rx.var
    def roles_description(self) -> str:
        return self.translate(
            de=textwrap.dedent("""
                - STUDENT: Kann Übungen ansehen und bearbeiten.
                - TUTOR: Kann zusätzlich Abgaben aller Nutzer einsehen.
                - ADMIN: Kann alles (Übungen anlegen, Benutzer verwalten...).
            """),
            en=textwrap.dedent("""
                - STUDENT: Can view and work on exercises.
                - TUTOR: Can also view submissions by all users.
                - ADMIN: Can do everything (create exercises, manage users...).
            """),
        )

    @rx.var
    def permissions(self) -> str:
        return self.translate(de="Berechtigungen", en="Permissions")

    @rx.var
    def admin_permission(self) -> str:
        return self.translate(de="Admin", en="Admin")

    @rx.var
    def maintainer_permission(self) -> str:
        return self.translate(de="Maintainer", en="Maintainer")

    @rx.var
    def lecturer_permission(self) -> str:
        return self.translate(de="Lecturer", en="Lecturer")

    # user settings --------------------------------------------------------------------
    @rx.var
    def user_settings(self) -> str:
        return self.translate(de="Benutzereinstellungen", en="User Settings")

    @rx.var
    def change_password(self) -> str:
        return self.translate(de="Passwort ändern", en="Change Password")

    @rx.var
    def current_password(self) -> str:
        return self.translate(de="Aktuelles Passwort", en="Current Password")

    # configuration page ---------------------------------------------------------------
    @rx.var
    def configuration(self) -> str:
        return self.translate(de="Konfiguration", en="Configuration")

    @rx.var
    def unsaved_changes_info(self) -> str:
        return self.translate(
            de="Sie haben ungespeicherte Änderungen.",
            en="You have unsaved changes.",
        )

    @rx.var
    def registration_code_info(self) -> str:
        return self.translate(
            de="Der Registrierungscode, den Studenten bei der Registrierung "
            "eingeben müssen.",
            en="The registration code that students have to enter during registration.",
        )

    @rx.var
    def course_name(self) -> str:
        return self.translate(de="Kursname", en="Course Name")

    @rx.var
    def response_ai_model(self) -> str:
        return self.translate(de="Antwort KI-Modell", en="Response AI Model")

    @rx.var
    def openai_api_model_info(self) -> str:
        return self.translate(
            de="""
Für Infos zu verfügbaren Modellen, bitte bei \
[openai](https://platform.openai.com/docs/models) nachschauen.  \n\
Der Modellname muss genau richtig eingegeben werden. Der korrekte Name \
lässt sich im Abschnitt `Snapshots` des jeweiligen Modells finden.  \n\
Beispiel: `gpt-4.1-mini`.  \n\
Bitte nach Änderung des Modells den Chat auf Funktionalität testen.
""",
            en="""
For info on available models, please refer to \
[openai](https://platform.openai.com/docs/models).  \n\
The model name must be entered exactly correctly. The correct name \
can be found in the `Snapshots` section of the respective model.  \n\
Example: `gpt-4.1-mini`.  \n\
Please test the chat for functionality after changing the model.
""",
        )

    @rx.var
    def response_ai_model_info(self) -> str:
        return self.translate(
            de=f"Das KI-Modell, welches im Chat antwortet.  \n\
            {self.openai_api_model_info}",
            en=f"The AI model that responds in the chat.  \n\
                {self.openai_api_model_info}",
        )

    @rx.var
    def check_ai_model(self) -> str:
        return self.translate(de="Überprüfungs-KI-Modell", en="Check AI Model")

    @rx.var
    def check_ai_model_info(self) -> str:
        return self.translate(
            de=f"Das KI-Modell, welches die Konversation überprüft.  \n\
                {self.openai_api_model_info}",
            en=f"The AI model that checks the conversation.  \n\
                {self.openai_api_model_info}",
        )

    @rx.var
    def check_conversation_prompt(self) -> str:
        return self.translate(
            de="Konversations-Überprüfungs-Prompt", en="Check Conversation Prompt"
        )

    @rx.var
    def check_conversation_prompt_info(self) -> str:
        return self.translate(
            de="Der Prompt, der verwendet wird, um die Konversation auf Korrektheit zu "
            "überprüfen.",
            en="The prompt used to check the conversation for correctness.",
        )

    @rx.var
    def how_to_use_text(self) -> str:
        return self.translate(
            de="How To Use Information",
            en="How To Use Information",
        )

    @rx.var
    def general_info_text(self) -> str:
        return self.translate(
            de="Allgemeine Informationen",
            en="General Information",
        )

    @rx.var
    def lecture_info_text(self) -> str:
        return self.translate(
            de="Informationen zur Vorlesung",
            en="Lecture Information",
        )

    @rx.var
    def info_texts_info(self) -> str:
        return self.translate(
            de="Diese Informationen werden auf der Startseite angezeigt. Wenn sie "
            "dieses Feld leer lassen, dann wird dieser Info Abschnitt nicht angezeigt. "
            "Der Text wird im Markdown-Format dargestellt.",
            en="These informations are shown on the home page. If you leave this "
            "field empty, this info section will not be displayed. "
            "The text is rendered in markdown format.",
        )

    @rx.var
    def impressum_info(self) -> str:
        return self.translate(
            de="Das Impressum soll die gesetzlich vorgeschriebenen Informationen über "
            "den Verantwortlichen der Webseite enthalten. "
            "Der Text wird im Markdown-Format dargestellt.",
            en="The impressum should contain the legally required information about "
            "the person responsible for the website. "
            "The text is rendered in markdown format.",
        )

    @rx.var
    def discard_changes(self) -> str:
        return self.translate(
            de="Änderungen verwerfen",
            en="Discard changes",
        )

    @rx.var
    def manage_prompts(self) -> str:
        return self.translate(
            de="Prompts verwalten",
            en="Manage Prompts",
        )

    @rx.var
    def prompt_variables_info(self) -> str:
        return self.translate(
            de="Sie können in Ihrem Prompt folgende Variablen verwenden: "
            "{title}, {description}, {lesson_context}. "
            "Die Variablen werden in der Übungsverwaltung gesetzt.",
            en="You can use the following variables in your prompt: "
            "{title}, {description}, {lesson_context}. "
            "The variables are set in the exercise management.",
        )

    @rx.var
    def add_prompt(self) -> str:
        return self.translate(
            de="Prompt hinzufügen",
            en="Add Prompt",
        )

    @rx.var
    def prompt_name(self) -> str:
        return self.translate(
            de="Prompt Name",
            en="Prompt Name",
        )

    @rx.var
    def delete_prompt(self) -> str:
        return self.translate(
            de="Prompt löschen",
            en="Delete Prompt",
        )

    @rx.var
    def delete_prompt_description(self) -> str:
        return self.translate(
            de="Möchten Sie diesen Prompt wirklich löschen? Der Prompt wird in "
            "existierenden Übungen durch den ausgewählten Ersatzprompt ersetzt.",
            en="Are you sure you want to delete this prompt? The prompt will be "
            "replaced in existing exercises by the selected replacement prompt.",
        )

    @rx.var
    def replacement_prompt(self) -> str:
        return self.translate(
            de="Ersatzprompt",
            en="Replacement Prompt",
        )

    @rx.var
    def prompt_name_placeholder(self) -> str:
        return self.translate(
            de="Einzigartiger Prompt Name",
            en="Unique prompt name",
        )

    @rx.var
    def mark_as_default_prompt(self) -> str:
        return self.translate(
            de="Als Standard Prompt markieren",
            en="Mark as default prompt",
        )

    @rx.var
    def default_prompt(self) -> str:
        return self.translate(
            de="Standard Prompt",
            en="Default prompt",
        )

    @rx.var
    def default_prompt_hover(self) -> str:
        return self.translate(
            de="Der Standard Prompt wird beim Hinzufügen einer Übung automatisch vorausgewählt, was Ihnen Zeit spart.",
            en="The default prompt will be automatically pre-selected when adding an exercise, saving you time.",
        )

    @rx.var
    def exercise_token_limit(self) -> str:
        return self.translate(
            de="Token-Limit pro Übung",
            en="Token limit per exercise",
        )

    @rx.var
    def exercise_token_limit_info(self) -> str:
        return self.translate(
            de=(
                "Maximale Anzahl von Tokens, die ein Nutzer für eine einzelne Übung "
                "verwenden darf. Bei Erreichen des Limits sind keine weiteren "
                "Nachrichten oder Checks möglich."
            ),
            en=(
                "Maximum number of tokens a user can spend on a single exercise. "
                "Once the limit is reached, no more messages or checks are allowed."
            ),
        )

    # Report Strings -------------------------------------------------------------------
    @rx.var
    def status(self) -> str:
        return self.translate(de="Status", en="Status")

    @rx.var
    def report_conversation(self) -> str:
        return self.translate(de="Konversation melden", en="Report conversation")

    @rx.var
    def report_problematic_chat(self) -> str:
        return self.translate(
            de="Problematischen Chat melden", en="Report problematic chat"
        )

    @rx.var
    def reports(self) -> str:
        return self.translate(de="Meldungen", en="Reports")

    @rx.var
    def report_placeholder(self) -> str:
        return self.translate(
            de="Melde hier Probleme wie eine unfaire Bewertung durch die KI, fehlerhafte Inhalte, unangemessene Antworten oder sonstige Auffälligkeiten...",
            en="Report issues here, such as unfair AI evaluations, incorrect content, inappropriate responses, or any other concerns...",
        )

    @rx.var
    def report_view(self) -> str:
        return self.translate(de="Anschauen", en="View")

    @rx.var
    def report_seen_tooltip(self) -> str:
        return self.translate(
            de="Dieser Bericht wurde gesehen", en="This report was seen"
        )

    @rx.var
    def report_not_seen_tooltip(self) -> str:
        return self.translate(
            de="Dieser Bericht wurde nicht gesehen", en="This report was not seen"
        )

    @rx.var
    def report_view_tooltip(self) -> str:
        return self.translate(
            de="Hier können Sie den Bericht ansehen", en="Here you can view the report"
        )

    @rx.var
    def delete_report_title(self) -> str:
        return self.translate(de="Bericht löschen", en="Delete Report")

    @rx.var
    def delete_report_content(self) -> str:
        return self.translate(
            de="Möchten Sie diesen Bericht wirklich löschen?",
            en="Are you sure you want to delete this report?",
        )

    @rx.var
    def deleted_report_title(self) -> str:
        return self.translate(
            de="[Gelöscht]",
            en="[Deleted]",
        )

    # ReportViewPage Strings -------------------------------------------------------------------

    @rx.var
    def report_message(self) -> str:
        return self.translate(de="Gemeldete Nachricht:", en="Report Message:")

    @rx.var
    def report_detail(self) -> str:
        return self.translate(de="Details zur Meldung", en="Report Details")

    @rx.var
    def report_mark_as_read(self) -> str:
        return self.translate(de="Als gelesen markieren", en="Mark as Read")

    @rx.var
    def report_mark_as_unread(self) -> str:
        return self.translate(de="Als ungelesen markieren", en="Mark as Unread")

    @rx.var
    def report_submitted_conversation(self) -> str:
        return self.translate(de="Eingereichter Chat:", en="Submitted Conversation:")

    # Edit Lecture Strings ------------------------------------------------------------------------
    @rx.var
    def edit_lecture(self) -> str:
        """The string for the 'Edit Lecture' tab."""
        return self.translate(de="Vorlesung bearbeiten", en="Edit Lecture")

    @rx.var
    def lecture_name(self) -> str:
        """Lecture name string."""
        return self.translate(de="Vorlesungsname", en="Lecture Name")

    @rx.var
    def create_lecture(self) -> str:
        """Create lecture button/title string."""
        return self.translate(de="Vorlesung erstellen", en="Create Lecture")

    @rx.var
    def save_lecture(self) -> str:
        """Save lecture button/title string."""
        return self.translate(de="Vorlesung speichern", en="Save Lecture")

    # My Lectures Strings -------------------------------------------------------------------------
    @rx.var
    def my_lectures(self) -> str:
        """The string for the 'My Lectures' tab/page."""
        return self.translate(de="Meine Vorlesungen", en="My Lectures")

    @rx.var
    def my_lectures_placeholder(self) -> str:
        """Placeholder text for the my lectures page skeleton."""
        return self.translate(
            de="Hier wird als Nächstes die Liste der Vorlesungen angezeigt, bei denen Sie Mitglied sind.",
            en="This page will next show the list of lectures you are a member of.",
        )

    @rx.var
    def no_joined_lectures(self) -> str:
        """Message shown when the user has not joined any lectures yet."""
        return self.translate(
            de="Sie sind aktuell in keiner Vorlesung Mitglied.",
            en="You have not joined any lectures yet.",
        )

    @rx.var
    def no_matching_lectures(self) -> str:
        """Message shown when no lectures match the current filter."""
        return self.translate(
            de="Keine Vorlesungen entsprechen dem aktuellen Filter.",
            en="No lectures match the current filter.",
        )

    @rx.var
    def all(self) -> str:
        """Label for all items."""
        return self.translate(de="Alle", en="All")

    @rx.var
    def not_joined(self) -> str:
        """Label for lectures without membership."""
        return self.translate(de="Nicht beigetreten", en="Not joined")

    @rx.var
    def owner_role(self) -> str:
        """Localized owner role label."""
        return self.translate(de="Besitzer", en="Owner")

    @rx.var
    def tutor_role(self) -> str:
        """Localized tutor role label."""
        return self.translate(de="Tutor", en="Tutor")

    @rx.var
    def student_role(self) -> str:
        """Localized student role label."""
        return self.translate(de="Student", en="Student")


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

    # MyLecturesState -------------------------------------------------------------

    @staticmethod
    def lecture_name_already_exists(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Dieser Vorlesungsname existiert bereits.",
            en="Error: This lecture name already exists.",
        )

    @staticmethod
    def enter_lecture_name(language: Language) -> str:
        return translate(
            language,
            de="Bitte geben Sie einen Vorlesungsnamen ein.",
            en="Please enter a lecture name.",
        )

    # ManageExercisesState -------------------------------------------------------------
    @staticmethod
    def tagname_already_exists(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Dieser Tag Name existiert bereits.",
            en="Error: This tag name already exists.",
        )

    @staticmethod
    def tag_renamed_successfully(language: Language) -> str:
        return translate(
            language,
            de="Tag erfolgreich umbenannt.",
            en="Tag renamed successfully.",
        )

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
            de="Tag erfolgreich hinzugefügt.",
            en="Tag has been added successfully.",
        )

    @staticmethod
    def changes_saved(language: Language) -> str:
        return translate(
            language,
            de="Änderungen erfolgreich gespeichert.",
            en="Changes saved successfully.",
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

    @staticmethod
    def selected_exercises_deleted(language: Language) -> str:
        return translate(
            language,
            de="Ausgewählte Übungen erfolgreich gelöscht",
            en="Selected exercises deleted successfully",
        )

    @staticmethod
    def successfully_imported_exercises(language: Language, count: int) -> str:
        return translate(
            language,
            de=f"{count} Übungen erfolgreich importiert.",
            en=f"{count} exercises imported successfully.",
        )

    @staticmethod
    def added_new_prompts(language: Language, prompt_list: str) -> str:
        return translate(
            language,
            de=f"Neue Prompts hinzugefügt: \n {prompt_list}",
            en=f"Added new prompts: \n {prompt_list}",
        )

    @staticmethod
    def added_and_renamed_conflicting_prompts(
        language: Language, prompt_list: str
    ) -> str:
        return translate(
            language,
            de=f"Konfliktierende Prompts hinzugefügt und umbenannt: \n {prompt_list}",
            en=f"Added and renamed conflicting prompts: \n {prompt_list}",
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

    @staticmethod
    def prompt_loading_error(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Der Prompt für diese Übung konnte nicht geladen werden.",
            en="Error: The prompt for this exercise could not be loaded.",
        )

    @staticmethod
    def successful_report_title(language: Language) -> str:
        return translate(language, de="Bericht gesendet", en="Report submitted")

    @staticmethod
    def successful_report_description(language: Language) -> str:
        return translate(
            language,
            de="Vielen Dank für Ihre Rückmeldung!",
            en="Thank you for your feedback!",
        )

    @staticmethod
    def no_report_message_title(language: Language) -> str:
        return translate(language, de="Bericht fehlgeschlagen", en="Report failed")

    @staticmethod
    def no_report_message_description(language: Language) -> str:
        return translate(
            language,
            de="Ein leerer Bericht kann nicht eingereicht werden.",
            en="Cannot submit empty report.",
        )

    # UserSettingsState ----------------------------------------------------------------

    @staticmethod
    def change_password_message_success(language: Language) -> str:
        return translate(
            language,
            de="Passwort geändert.",
            en="Password Changed.",
        )

    @staticmethod
    def change_password_message_current_does_not_match(language: Language) -> str:
        return translate(
            language,
            de="Aktuelles Passwort ist falsch.",
            en="Current password is wrong.",
        )

    @staticmethod
    def change_password_message_confirmed_does_not_match(language: Language) -> str:
        return translate(
            language,
            de="'Neues' und 'bestätigtes' Passwort stimmen nicht überein.",
            en="'New' and 'Confirmed' password do not match.",
        )

    # ConfigurationState ---------------------------------------------------------------

    @staticmethod
    def config_saved(language: Language) -> str:
        return translate(
            language,
            de="Konfiguration erfolgreich gespeichert.",
            en="Configuration saved successfully.",
        )

    @staticmethod
    def prompts_saved(language: Language) -> str:
        return translate(
            language,
            de="Prompts erfolgreich gespeichert.",
            en="Prompts saved successfully.",
        )

    @staticmethod
    def prompt_added(language: Language) -> str:
        return translate(
            language,
            de="Prompt erfolgreich hinzugefügt.",
            en="Prompt added successfully.",
        )

    @staticmethod
    def prompt_names_unique_error(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Prompt Namen müssen eindeutig sein.",
            en="Error: Prompt names must be unique.",
        )

    @staticmethod
    def prompt_names_nonempty_error(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Prompt Namen dürfen nicht leer sein.",
            en="Error: Prompt names must not be empty.",
        )

    @staticmethod
    def prompt_deleted(language: Language) -> str:
        return translate(
            language,
            de="Prompt erfolgreich gelöscht.",
            en="Prompt deleted successfully.",
        )

    @staticmethod
    def replacement_prompt_not_found(language: Language) -> str:
        return translate(
            language,
            de="Fehler: Ersatzprompt nicht gefunden.",
            en="Error: Replacement prompt not found.",
        )
