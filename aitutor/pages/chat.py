"""This module contains the chat component."""

from typing import Optional, cast

import reflex as rx
import decouple
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

import aitutor.routes as routes
from aitutor.config import get_config
from aitutor.pages.navbar import with_navbar
from aitutor.models import Exercise, ExerciseResult
from aitutor.auth.protection import require_role_at_least
from aitutor.models import UserRole
from aitutor.auth.state import SessionState
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_MODEL = "gpt-4o-mini"
CHECK_RESULT_ROLE: str = "check_result"
TIME_FORMAT = "%d.%m.%Y %H:%M:%S MEZ"
TIME_ZONE = "Europe/Berlin"


async def get_chat_response(conversation):
    """
    Sends asynchronous requests to OpenAI.

    conversation: Expects list of dictionaries of the previous messages between ChatGPT
    and the user.
    """
    # I use python decouple to retrieve the API Key, can also use os.
    # TODO: Do we really need decouple here? What's the advantage?
    API_KEY = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=None))
    if not API_KEY:
        raise ValueError("API key not found.")

    # Creates GPT instance
    client = AsyncOpenAI(api_key=API_KEY)
    # filter out messages with role 'check_result' from the conversation
    conversation = [msg for msg in conversation if msg["role"] != CHECK_RESULT_ROLE]
    # remove msg["check_passed"] from conversation
    for msg in conversation:
        if "check_passed" in msg:
            del msg["check_passed"]
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


class CheckConversationResponse(BaseModel):
    """
    Represents the response structure for checking a conversation.,
    including an explanation and pass status.
    """

    explanation: str
    check_passed: bool


async def get_check_conversation_response(
    conversation,
) -> CheckConversationResponse | None:
    """
    Sends request to OpenAI.

    conversation: Expects list of dictionaries of the previous messages between ChatGPT
    and the user.
    """
    config = get_config()
    check_conversation_prompt = config.check_conversation_prompt.prompt
    if not check_conversation_prompt:
        raise ValueError("Check Conversation prompt not set in config.")

    # filter out messages with role 'check_result' from the conversation
    conversation = [msg for msg in conversation if msg["role"] != CHECK_RESULT_ROLE]
    # remove msg["check_passed"] from conversation
    for msg in conversation:
        if "check_passed" in msg:
            del msg["check_passed"]
    conversation.append(
        {
            "role": "system",
            "content": check_conversation_prompt,
        }
    )
    API_KEY = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=None))
    if not API_KEY:
        raise ValueError("API key not found.")
    client = OpenAI(api_key=API_KEY)
    response = client.responses.parse(
        model=DEFAULT_MODEL,
        input=conversation,
        text_format=CheckConversationResponse,
    )
    return response.output_parsed


class ChatMessage(rx.Base):
    """
    Class to make handling ChatMessages easier and help differentiate between authors of
    chat messages.
    """

    message: str
    is_llm: bool = False
    is_check_result: bool = False
    # check_passed is used to color the check result message
    check_passed: bool = False


class ChatState(SessionState):
    """Handles the ChatState."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    exercise_title: str = "No Exercise Selected"
    system_message_gpt: str
    check_is_loading: bool = False
    waiting_for_response: bool = False
    check_passed: bool = False
    conversation_is_submitted: bool = False
    submit_time_stamp: str = ""

    @rx.var
    def finished_view_url(self) -> str:
        """
        The exercise_id is used to identify the current exercise.
        It is set by the route parameter in the URL.
        """
        return f"{routes.FINISHED_VIEW}/{self.router.page.params.get('exercise_id', 0)}"

    @rx.event
    def load_exercise(self):
        """
        Loads the exercise with exercise_id from the database.
        """
        with rx.session() as session:
            exercise = session.exec(
                Exercise.select().where(Exercise.id == self.exercise_id)
            ).one_or_none()
            exercise_result = session.exec(
                ExerciseResult.select().where(
                    ExerciseResult.exercise_id == self.exercise_id,
                    ExerciseResult.userinfo_id == self.user_id,
                )
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
                yield rx.redirect(routes.NOT_FOUND)
            if exercise_result:
                self.check_passed = exercise_result.check_passed
                self.conversation_is_submitted = (
                    exercise_result.finished_conversation != []
                )
                self.submit_time_stamp = (
                    exercise_result.submit_time_stamp.strftime(TIME_FORMAT)
                    if exercise_result.submit_time_stamp
                    else ""
                )
            else:
                self.check_passed = False
                self.conversation_is_submitted = False
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
                        if msg["role"] in ["user", "assistant", CHECK_RESULT_ROLE]:
                            self.append_chat_message(
                                msg["content"],
                                is_llm=(msg["role"] == "assistant"),
                                is_check_result=(msg["role"] == CHECK_RESULT_ROLE),
                                check_passed=msg.get("check_passed", False),
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

    def do_nothing(self):
        """
        Placeholder function to do nothing.
        """
        pass

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
                ).one_or_none()

                if exercise_result:
                    if exercise_result.finished_conversation == []:
                        # delete conversation from db if there is nothing submitted yet
                        session.delete(exercise_result)
                        session.commit()
                    else:
                        # only reset conversation_text and check_passed if there
                        # is already a finished conversation
                        exercise_result.conversation_text = []
                        exercise_result.check_passed = False
                        session.commit()

        # Only reset the conversation if there are messages beyond the initial message
        # by ChatGPT.
        self.check_passed = False
        if len(self.messages) > 1:
            self.messages = []
            if self.current_exercise:
                self.append_chat_message(self.current_exercise.description, is_llm=True)

    def append_chat_message(
        self,
        message,
        is_llm: bool = False,
        is_check_result: bool = False,
        check_passed: bool = False,
    ):
        """
        Once a new message is generated by the user it is appended to the list of
        messages in ChatState.
        """
        self.messages.append(
            ChatMessage(
                message=message,
                is_llm=is_llm,
                is_check_result=is_check_result,
                check_passed=check_passed,
            )
        )

    @rx.event
    async def send_message(self, form_data: dict):
        """
        New messages get appended to list of ChatMessages.
        """
        user_message = form_data.get("user_response")
        if user_message:
            self.append_chat_message(message=user_message, is_llm=False)
            self.waiting_for_response = True
            yield
            # Takes list of ChatMessage and turns into a list of dictionaries, so
            # the OpenAI API can handle the messages.
            messages = self.get_messages_dict_gpt()
            # Wait while OpenAI Response is generated.
            llm_response = await get_chat_response(conversation=messages)
            # Append response generated by LLM to list of messages, set is_llm to
            # True to indicate that it is generated by the user.
            self.append_chat_message(message=llm_response, is_llm=True)
            messages = self.get_messages_dict_gpt()
            self.waiting_for_response = False
            yield

            # Save conversation to database.
            self.save_conversation_to_db(conversation=messages)

    def successfull_submit_message(self):
        """
        show success message if check is passed.
        """
        return rx.toast.success(
            title="Submit",
            description="Your conversation was submitted successfully.",
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    @rx.event
    async def check_conversation(self):
        """
        Check the conversation of the user.
        """
        conversation = self.get_messages_dict_gpt()
        self.check_is_loading = True
        yield
        check_conversation_response = await get_check_conversation_response(
            conversation
        )
        self.check_is_loading = False
        self.check_passed = (
            check_conversation_response.check_passed
            if check_conversation_response
            else False
        )

        # show explanation of the check in the chat
        check_status: str = "✅ Passed" if self.check_passed else "❌ Failed"
        if check_conversation_response is not None:
            self.append_chat_message(
                message="# Check Result: "
                + check_status
                + "\n"
                + "🛈 _This result is not part of the conversation, "
                + "meaning the AI cannot see it._\n\n"
                + check_conversation_response.explanation,
                is_llm=True,
                is_check_result=True,
                check_passed=self.check_passed,
            )
        conversation = self.get_messages_dict_gpt()
        self.save_conversation_to_db(conversation=conversation)

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
                ).one_or_none()

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
                        check_passed=self.check_passed,
                    )
                    session.add(exercise_result)
                    session.commit()
                else:
                    # update existing ExerciseResult
                    exercise_result.conversation_text = conversation
                    exercise_result.check_passed = self.check_passed
                    session.commit()

    @rx.event
    def submit_conversation(self):
        """
        Saves the finished conversation to the database.
        """
        if self.check_passed:
            conversation = self.get_messages_dict_gpt()
            userinfo_id: Optional[int] = self.user_id
            if self.current_exercise and userinfo_id:
                with rx.session() as session:
                    exercise_result = session.exec(
                        ExerciseResult.select().where(
                            ExerciseResult.exercise_id == self.current_exercise.id,
                            ExerciseResult.userinfo_id == userinfo_id,
                        )
                    ).one_or_none()

                    if exercise_result is not None:
                        # update existing ExerciseResult
                        exercise_result.finished_conversation = conversation
                        exercise_result.submit_time_stamp = datetime.now(
                            ZoneInfo(TIME_ZONE)
                        )
                        session.commit()
                        yield self.successfull_submit_message()
                    else:
                        raise ValueError(
                            "There is no ExerciseResult to save the "
                            "finished conversation to."
                        )
            self.conversation_is_submitted = True
            self.submit_time_stamp = datetime.now(ZoneInfo(TIME_ZONE)).strftime(
                TIME_FORMAT
            )

    def get_messages_dict_gpt(self):
        """
        This functions iterates over all previous chat messages and reformats them as a
        list of dictionaries, so they can be handed to the OpenAI-API.
        """
        # Initialize GPT with the desired role, for now GPT acts as a generic tutor.
        # TODO Initialization should change depending on the exercises.
        messages_gpt = [
            {
                "role": "system",
                "content": self.system_message_gpt,
                "check_passed": False,
            }
        ]
        # Iterate through all message, create dictionary for each message and append
        # them to list of dictionaries.
        for chat_message in self.messages:
            role = "user"
            if chat_message.is_llm:
                role = "assistant"
            if chat_message.is_check_result:
                role = CHECK_RESULT_ROLE
            messages_gpt.append(
                {
                    "role": role,
                    "content": chat_message.message,
                    "check_passed": chat_message.check_passed,
                }
            )
        return messages_gpt


def message_box(chat_message: ChatMessage) -> rx.Component:
    """Each message from the chat history gets its bounding box. Depending on the sender
    the message is aligned to the left for the LLM and aligned to the right for the
    user.
    """
    check_result_color = rx.cond(
        chat_message.check_passed,
        "green",
        "yellow",
    )
    return rx.box(
        rx.box(
            rx.markdown(
                chat_message.message,
                background_color=rx.cond(
                    chat_message.is_check_result,
                    rx.color(check_result_color, 4),
                    rx.cond(
                        chat_message.is_llm, rx.color("mauve", 4), rx.color("iris", 4)
                    ),
                ),
                color=rx.cond(
                    chat_message.is_check_result,
                    rx.color(check_result_color, 12),
                    rx.cond(
                        chat_message.is_llm, rx.color("mauve", 12), rx.color("iris", 12)
                    ),
                ),
                display="inline-block",
                padding="1em",
                border_radius="8px",
                max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
            ),
            text_align=rx.cond(
                chat_message.is_check_result,
                "left",
                rx.cond(chat_message.is_llm, "left", "right"),
            ),
            margin_top="1em",
        ),
        width="100%",
    )


def chat_form() -> rx.Component:
    """
    Render the chat form for user input. Includes button to send Reply and button to
    check the conversation.
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
                rx.hstack(
                    reset_conversation_button(),
                    check_conversation_button(),
                ),
                send_message_button(),
                width="100%",
                justify="between",
            ),
        ),
        on_submit=ChatState.send_message,
        reset_on_submit=True,
    )


def send_message_button() -> rx.Component:
    """
    Render the button to send a message.
    """
    return rx.button(
        rx.icon("send-horizontal", size=20),
        type="submit",
        color_scheme="iris",
        _hover=rx.cond(
            ChatState.waiting_for_response,
            {"cursor": "not-allowed"},
            {"cursor": "pointer"},
        ),
        loading=ChatState.waiting_for_response,
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
                    rx.cond(
                        ChatState.conversation_is_submitted,
                        "Are you sure you want to reset the conversation? "
                        + "(This will not delete your submission.)",
                        "Are you sure you want to reset the conversation? ",
                    )
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


def check_conversation_button() -> rx.Component:
    """
    Render the button to check the conversation.
    """
    return rx.cond(
        ChatState.check_passed,
        rx.button(
            "Submit",
            color_scheme="green",
            type="button",
            _hover={"cursor": "pointer"},
            on_click=ChatState.submit_conversation,
        ),
        rx.cond(
            ChatState.check_is_loading,
            rx.button(
                "Check Conversation",
                color_scheme="yellow",
                type="button",
                _hover={"cursor": "not-allowed"},
                loading=True,
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        "Check Conversation",
                        color_scheme="yellow",
                        type="button",
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
                    ),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Check Conversation"),
                    rx.alert_dialog.description(
                        "Are you done with the exercise and want "
                        + "to check your conversation?"
                    ),
                    rx.hstack(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "No",
                                color_scheme="red",
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Yes",
                                color_scheme="iris",
                                on_click=ChatState.check_conversation,
                                _hover={"cursor": "pointer"},
                            ),
                        ),
                        margin_top="1em",
                    ),
                ),
            ),
        ),
    )


def submitted_status() -> rx.Component:
    """
    Render the status when the conversation is submitted.
    """
    return rx.hstack(
        rx.hover_card.root(
            rx.hover_card.trigger(
                rx.button(
                    rx.icon("eye", size=20),
                    color_scheme="iris",
                    on_click=rx.redirect(ChatState.finished_view_url),
                    _hover={"cursor": "pointer"},
                ),
            ),
            rx.hover_card.content(
                rx.text("View your submitted conversation"),
            ),
        ),
        rx.text(
            "Last submit: " + ChatState.submit_time_stamp,
            color_scheme="green",
        ),
        rx.icon(
            "circle-check",
            color="green",
            size=30,
        ),
        align="center",
    )


def not_submitted_status() -> rx.Component:
    """
    Render the status when the conversation is not submitted yet.
    """
    return rx.hstack(
        rx.icon(
            "info",
            color=rx.color_mode_cond(light="black", dark="white"),
            size=20,
        ),
        rx.text("Not submitted yet"),
        spacing="1",
        align="center",
    )


def show_exercise_status() -> rx.Component:
    """
    Show the status of the exercise, whether it is submitted or not.
    """
    return rx.cond(
        ChatState.conversation_is_submitted,
        submitted_status(),
        not_submitted_status(),
    )


@with_navbar
@require_role_at_least(UserRole.STUDENT)
def chat_default() -> rx.Component:
    """Renders the web page."""
    return rx.container(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=20),
                            color_scheme="iris",
                            on_click=rx.redirect(routes.EXERCISES),
                            _hover={"cursor": "pointer"},
                        ),
                        rx.heading(
                            "Exercise: " + ChatState.exercise_title,
                            size="5",
                        ),
                        align="center",
                    ),
                    show_exercise_status(),
                    align="center",
                    justify="between",
                    width="100%",
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
