"""This module contains the chat component."""

from typing import Optional, cast

import reflex as rx
from decouple import config
from openai import AsyncOpenAI

from aitutor.pages.navbar import with_navbar
from aitutor.models import Exercise, ExerciseResult
from aitutor.auth.protection import require_role_at_least
from aitutor.models import UserRole
from aitutor.auth.state import SessionState

DEFAULT_MODEL = "gpt-4o-mini"


async def get_response(conversation):
    """
    Sends asynchronous requests to OpenAI.

    conversation: Expects list of dictionaries of the previous messages between ChatGPT
    and the user.
    """
    # I use python decouple to retrieve the API Key, can also use os.
    # TODO: Do we really need decouple here? What's the advantage?
    API_KEY = cast(str, config("OPENAI_API_KEY", cast=str, default=None))
    if not API_KEY:
        raise ValueError("API key not found.")

    # Creates GPT instance
    client = AsyncOpenAI(api_key=API_KEY)
    # Wait till Chat Completion Request is fulfilled.
    session = await client.chat.completions.create(
        model=DEFAULT_MODEL, messages=conversation
    )
    # Extracts the first response by CHATGPT. By default only a single response is
    # generated.
    response = session.choices[0].message.content
    if not isinstance(response, str):
        raise TypeError(f"Expected string but got {type(response)}: {response}")
    return response


class ChatMessage(rx.Base):
    """
    Class to make handling ChatMessages easier and help differentiate between authors of
    chat messages.
    """

    message: str
    is_llm: bool = False


class ChatState(SessionState):
    """Handles the ChatState."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    exercise_title: str = "No Exercise Selected"
    system_message_gpt: str

    @rx.event
    def load_exercise(self):
        """
        Loads the exercise with exercise_id from the database.
        """
        with rx.session() as session:
            exercise = session.exec(
                Exercise.select().where(Exercise.id == self.exercise_id)
            ).one_or_none()
            if exercise:
                self.current_exercise = exercise
                self.exercise_title = self.current_exercise.title
                self.system_message_gpt = self.current_exercise.prompt
                self.messages = []
                self.load_existing_conversation()
                if not self.messages:
                    self.append_chat_message(
                        self.current_exercise.description, is_llm=True
                    )
            else:
                raise ValueError("Exercise not found in database.")
        yield

    def load_existing_conversation(self):
        """
        Loads existing conversation from database.
        """
        userinfo_id: Optional[int] = self.user_id
        if self.current_exercise and userinfo_id:
            with rx.session() as session:
                exercise_result = session.exec(
                    ExerciseResult.select().where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == userinfo_id,
                    )
                ).one_or_none()

                if exercise_result:
                    for msg in exercise_result.conversation_text:
                        if msg["role"] in ["user", "assistant"]:
                            self.append_chat_message(
                                msg["content"], is_llm=(msg["role"] == "assistant")
                            )

    def no_exercise_available(self):
        """Sends chat message to user if no exercises are available."""
        self.messages = []
        self.append_chat_message(
            "There are no exercises yet. Please wait till exercises are added.",
            is_llm=True,
        )

    def chat_not_available(self):
        """
        Replies to chat message of user if no exercises are available or no
        exercise has been selected. Also prevents unnecessary use of OpenAI API.
        """
        self.append_chat_message(
            message="Chatting is unavailable while no exercises are available "
            + "or no exercise is selected.",
            is_llm=True,
        )

    @rx.event
    def reset_conversation(self):
        """Resets conversation for current exercise."""
        # delete conversation from database
        userinfo_id: Optional[int] = self.user_id
        if self.current_exercise and userinfo_id:
            with rx.session() as session:
                exercise_result = session.exec(
                    ExerciseResult.select().where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == userinfo_id,
                    )
                ).all()

                if exercise_result:
                    for result in exercise_result:
                        session.delete(result)
                    session.commit()
        # Only reset the conversation if there are messages beyond the initial message
        # by ChatGPT.
        if len(self.messages) > 1:
            self.messages = []
            if not self.messages and self.current_exercise:
                self.append_chat_message(self.current_exercise.description, is_llm=True)

    def append_chat_message(self, message, is_llm: bool = False):
        """
        Once a new message is generated by the user it is appended to the list of
        messages in ChatState.
        """
        self.messages.append(ChatMessage(message=message, is_llm=is_llm))

    @rx.event
    async def send_message(self, form_data: dict):
        """
        New messages get appended to list of ChatMessages.
        """
        user_message = form_data.get("user_response")
        if user_message:
            self.append_chat_message(message=user_message, is_llm=False)
            yield
            # Takes list of ChatMessage and turns into a list of dictionaries, so
            # the OpenAI API can handle the messages.
            messages = self.get_messages_dict_gpt()
            # Wait while OpenAI Response is generated.
            llm_response = await get_response(conversation=messages)
            # Append response generated by LLM to list of messages, set is_llm to
            # True to indicate that it is generated by the user.
            self.append_chat_message(message=llm_response, is_llm=True)
            messages = self.get_messages_dict_gpt()
            yield

            # Save conversation to database.
            self.save_conversation_to_db(conversation=messages)

    def save_conversation_to_db(self, conversation: list[dict]):
        """
        Saves the conversation to the database.
        """
        userinfo_id: Optional[int] = self.user_id
        if self.current_exercise and userinfo_id:
            with rx.session() as session:
                exercise_result = session.exec(
                    ExerciseResult.select().where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == userinfo_id,
                    )
                ).first()

                if exercise_result is None:
                    # create new ExerciseResult if none exists
                    if self.current_exercise.id is None:
                        raise ValueError(
                            "Failed to save conversation because exercise_id is None."
                        )
                    exercise_result = ExerciseResult(
                        exercise_id=self.current_exercise.id,
                        userinfo_id=userinfo_id,
                        conversation_text=conversation,
                    )
                    session.add(exercise_result)
                    session.commit()
                else:
                    # update existing ExerciseResult
                    exercise_result.conversation_text = conversation
                    session.commit()

    def get_messages_dict_gpt(self):
        """
        This functions iterates over all previous chat messages and reformats them as a
        list of dictionaries, so they can be handed to the OpenAI-API.
        """
        # Initialize GPT with the desired role, for now GPT acts as a generic tutor.
        # TODO Initialization should change depending on the exercises.
        messages_gpt = [{"role": "system", "content": self.system_message_gpt}]
        # Iterate through all message, create dictionary for each message and append
        # them to list of dictionaries.
        for chat_message in self.messages:
            role = "user"
            if chat_message.is_llm:
                role = "assistant"
            messages_gpt.append({"role": role, "content": chat_message.message})
        return messages_gpt


def message_box(chat_message: ChatMessage) -> rx.Component:
    """Each message from the chat history gets its bounding box. Depending on the sender
    the message is aligned to the left for the LLM and aligned to the right for the
    user.
    """
    return rx.box(
        rx.box(
            rx.markdown(
                chat_message.message,
                background_color=rx.cond(
                    chat_message.is_llm, rx.color("mauve", 4), rx.color("iris", 4)
                ),
                color=rx.cond(
                    chat_message.is_llm, rx.color("mauve", 12), rx.color("iris", 12)
                ),
                display="inline-block",
                padding="1em",
                border_radius="8px",
                max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
            ),
            text_align=rx.cond(chat_message.is_llm, "left", "right"),
            margin_top="1em",
        ),
        width="100%",
    )


def chat_form() -> rx.Component:
    """
    Render the chat form for user input. Includes button to send Reply and button to
    check the answer.
    """
    return rx.form(
        rx.vstack(
            rx.text_area(
                name="user_response",
                placeholder="Your Answer",
                required=True,
                width="100%",
                color_scheme="iris",
                enter_key_submit=True,
            ),
            rx.hstack(
                reset_conversation_button(),
                rx.button(
                    "Send",
                    type="submit",
                    color_scheme="iris",
                    _hover={"cursor": "pointer"},
                ),
                width="100%",
                justify="between",
            ),
        ),
        on_submit=ChatState.send_message,
        reset_on_submit=True,
    )


def reset_conversation_button() -> rx.Component:
    """
    Render the button to reset the conversation.
    """
    return (
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.button(
                    "Reset Conversation",
                    color_scheme="red",
                    _hover=rx.cond(
                        ChatState.messages.length() < 2,  # type: ignore
                        {"cursor": "not-allowed"},
                        {"cursor": "pointer"},
                    ),
                    disabled=rx.cond(
                        ChatState.messages.length() < 2,  # type: ignore
                        True,
                        False,
                    ),
                )
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("Reset Conversation"),
                rx.alert_dialog.description(
                    "Are you sure you want to reset the conversation?"
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancel",
                            color_scheme="red",
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Confirm",
                            color_scheme="iris",
                            on_click=ChatState.reset_conversation,
                            _hover={"cursor": "pointer"},
                        ),
                    ),
                    margin_top="1em",
                ),
            ),
        ),
    )


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def chat_default() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.heading(
                    "Exercise: " + ChatState.exercise_title,
                    size="5",
                ),
                rx.auto_scroll(
                    rx.foreach(
                        ChatState.messages,
                        message_box,
                    ),
                    scroll_to_bottom_on_update=True,
                    width="100%",
                    flex="1",
                    padding_right="8px",
                ),
                chat_form(),
                spacing="5",
                justify="start",
                min_height="85vh",
                max_height="85vh",
                height="100%",
            ),
            width="100%",
        ),
        align_items="center",
        width="100%",
    )
