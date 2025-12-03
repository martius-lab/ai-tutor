"""The state of the chat page."""

from datetime import datetime
from enum import StrEnum
from typing import Optional, cast
from zoneinfo import ZoneInfo

import decouple
import reflex as rx
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from sqlmodel import select

import aitutor.routes as routes
from aitutor.auth.protection import state_require_role_at_least
from aitutor.auth.state import SessionState
from aitutor.config import get_config
from aitutor.global_vars import TIME_FORMAT, TIME_ZONE
from aitutor.language_state import BackendTranslations as BT
from aitutor.models import Exercise, ExerciseResult, UserRole


class Role(StrEnum):
    """
    Enum to represent the role of a message in the conversation.
    """

    # do not change these role names. They are used in the OpenAI API.
    USER = "user"
    AITUTOR = "assistant"
    SYSTEM = "system"

    # this role name can be changed freely.
    CHECK_RESULT = "check_result"


class ChatMessage(BaseModel):
    """
    Class to make handling ChatMessages easier and help differentiate between authors of
    chat messages.
    """

    message: str
    role: Role
    # check_passed is used to color the check result message
    check_passed: bool = False


class CheckConversationResponse(BaseModel):
    """
    Represents the response structure for checking a conversation.,
    including an explanation and pass status.
    """

    explanation: str
    check_passed: bool


async def get_chat_response(conversation):
    """
    Sends asynchronous requests to OpenAI.

    conversation: Expects list of dictionaries of the previous messages between ChatGPT
    and the user.
    """
    API_KEY = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if API_KEY == "":
        raise ValueError("API key not found.")

    # Creates GPT instance
    client = AsyncOpenAI(api_key=API_KEY)
    # filter out messages with role 'check_result' from the conversation
    conversation = [
        msg for msg in conversation if msg["role"] != Role.CHECK_RESULT.value
    ]
    # remove msg["check_passed"] from conversation
    for msg in conversation:
        if "check_passed" in msg:
            del msg["check_passed"]
    # Wait till Chat Completion Request is fulfilled.
    session = await client.chat.completions.create(
        model=get_config().response_ai_model, messages=conversation
    )
    # Extracts the first response by CHATGPT. By default only a single response is
    # generated.
    response = session.choices[0].message.content
    if not isinstance(response, str):
        raise TypeError(f"Expected string but got {type(response)}: {response}")
    return response


async def get_check_conversation_response(
    conversation,
) -> CheckConversationResponse | None:
    """
    Sends request to OpenAI.

    conversation: Expects list of dictionaries of the previous messages between ChatGPT
    and the user.
    """
    config = get_config()
    check_conversation_prompt = config.check_conversation_prompt
    if not check_conversation_prompt:
        raise ValueError("Check Conversation prompt not set in config.")

    # filter out messages with role 'check_result' from the conversation
    conversation = [
        msg for msg in conversation if msg["role"] != Role.CHECK_RESULT.value
    ]
    # remove msg["check_passed"] from conversation
    for msg in conversation:
        if "check_passed" in msg:
            del msg["check_passed"]
    conversation.append(
        {
            "role": Role.SYSTEM.value,
            "content": check_conversation_prompt,
        }
    )
    API_KEY = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if API_KEY == "":
        raise ValueError("API key not found.")
    client = OpenAI(api_key=API_KEY)
    response = client.responses.parse(
        model=config.check_ai_model,
        input=conversation,
        text_format=CheckConversationResponse,
    )
    return response.output_parsed


class ChatState(SessionState):
    """Handles the ChatState."""

    messages: list[ChatMessage] = []
    current_exercise: Optional[Exercise] = None
    exercise_title: str = "No Exercise Selected"
    system_message_gpt: str
    waiting_for_response: bool = False
    check_passed: bool = False
    conversation_is_submitted: bool = False
    submit_time_stamp: str = ""
    user_input: str = ""
    last_user_message_index: int = -1
    is_overdue: bool = False

    _userinfo_id: int = -1

    @rx.event
    def set_user_input(self, value: str):
        """Sets the user input value."""
        self.user_input = value

    @rx.event
    @state_require_role_at_least(UserRole.STUDENT)
    def on_load(self):
        """
        Loads the exercise with exercise_id from the database.
        And sets all button loading states to False.
        """

        self.global_load()
        self.waiting_for_response = False

        userinfo = self.authenticated_user_info
        # should be guaranteed by the decorator but assert for type checkers
        assert userinfo is not None and userinfo.id is not None
        self._userinfo_id = userinfo.id

        with rx.session() as session:
            exercise = session.exec(
                select(Exercise).where(Exercise.id == int(self.exercise_id))
            ).one_or_none()
            exercise_result = session.exec(
                select(ExerciseResult).where(
                    ExerciseResult.exercise_id == int(self.exercise_id),
                    ExerciseResult.userinfo_id == self._userinfo_id,
                )
            ).one_or_none()
            error_when_loading_prompt: bool = False
            if exercise:
                self.current_exercise = exercise
                self.exercise_title = self.current_exercise.title
                self.is_overdue = self.current_exercise.deadline_exceeded

                if self.current_exercise.prompt:
                    exercise_prompt = self.current_exercise.prompt.prompt_template
                else:
                    exercise_prompt = (
                        "tell the user there was an error when loading "
                        "the prompt. Don't answer any questions."
                    )
                    error_when_loading_prompt = True
                self.system_message_gpt = exercise_prompt.format(
                    title=self.current_exercise.title,
                    description=self.current_exercise.description,
                    lesson_context=self.current_exercise.lesson_context,
                )

                self.messages = []
                self.load_existing_conversation()
                if not self.messages:
                    self.append_chat_message(
                        self.current_exercise.description,
                        role=Role.AITUTOR,
                        check_passed=False,
                    )
                self.update_last_user_message_index()
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
        if error_when_loading_prompt:
            yield rx.toast.error(
                description=BT.prompt_loading_error(self.language),
                duration=5000,
                position="bottom-center",
                invert=True,
            )
            error_when_loading_prompt = False
        else:
            yield

    def on_logout(self):
        """Clears the state when the user logs out."""
        self.messages = []
        self.current_exercise = None
        self.exercise_title = "No Exercise Selected"
        self.system_message_gpt = ""
        self.waiting_for_response = False
        self.check_passed = False
        self.conversation_is_submitted = False
        self.submit_time_stamp = ""
        self.user_input = ""
        self.last_user_message_index = -1
        self.is_overdue = False
        self._userinfo_id = -1

    @rx.var
    def finished_view_url(self) -> str:
        """
        The exercise_id is used to identify the current exercise.
        It is set by the route parameter in the URL.
        """
        return f"{routes.FINISHED_VIEW}/{self.exercise_id}"

    @rx.event
    def edit_last_message(self):
        """
        Deletes the last user message in the chat and every message after it.
        And copys the last user message to the input field.
        """
        check_already_passed = False
        # state changes
        for i in reversed(range(len(self.messages))):
            msg = self.messages[i]
            if msg.role == Role.USER.value:
                self.user_input = msg.message
                check_already_passed = msg.check_passed
                del self.messages[i:]
                break
        self.check_passed = check_already_passed
        self.update_last_user_message_index()

        # update db
        self.save_conversation_to_db(conversation=self.get_messages_dict_gpt())

    @rx.event
    def reset_conversation(self):
        """Resets conversation for current exercise."""
        # delete conversation from database
        if self.current_exercise:
            with rx.session() as session:
                exercise_result = session.exec(
                    select(ExerciseResult).where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == self._userinfo_id,
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
        self.user_input = ""
        if len(self.messages) > 1:
            self.messages = []
            if self.current_exercise:
                self.append_chat_message(
                    self.current_exercise.description,
                    role=Role.AITUTOR,
                    check_passed=False,
                )

    @rx.event(background=True)
    async def send_message(self, form_data: dict):
        """
        New messages get appended to list of ChatMessages.
        """
        async with self:
            if self.waiting_for_response:
                # don't allow sending another message while waiting for a response
                return
            self.waiting_for_response = True

        if self.user_input:
            async with self:
                self.append_chat_message(
                    message=self.user_input,
                    role=Role.USER,
                    check_passed=self.check_passed,
                )
                self.user_input = ""
            yield

            # Takes list of ChatMessage and turns into a list of dictionaries, so
            # the OpenAI API can handle the messages.
            messages = self.get_messages_dict_gpt()
            # Wait while OpenAI Response is generated.
            llm_response = await get_chat_response(conversation=messages)

            async with self:
                # Append response generated by LLM to list of messages, set is_llm to
                # True to indicate that it is generated by the user.
                self.append_chat_message(
                    message=llm_response,
                    role=Role.AITUTOR,
                    check_passed=self.check_passed,
                )
                self.update_last_user_message_index()
                messages = self.get_messages_dict_gpt()
            yield

            # Save conversation to database.
            async with self:
                self.save_conversation_to_db(conversation=messages)
                self.waiting_for_response = False

    @rx.event(background=True)
    async def check_conversation(self):
        """
        Check the conversation of the user.
        """
        async with self:
            self.waiting_for_response = True
            conversation = self.get_messages_dict_gpt()
        yield
        check_conversation_response = await get_check_conversation_response(
            conversation
        )
        async with self:
            self.waiting_for_response = False
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
                    role=Role.CHECK_RESULT,
                    check_passed=self.check_passed,
                )
            conversation = self.get_messages_dict_gpt()
            self.save_conversation_to_db(conversation=conversation)

    @rx.event
    def submit_conversation(self):
        """
        Saves the finished conversation to the database.
        """
        if self.check_passed:
            conversation = self.get_messages_dict_gpt()
            if self.current_exercise:
                with rx.session() as session:
                    exercise_result = session.exec(
                        select(ExerciseResult).where(
                            ExerciseResult.exercise_id == self.current_exercise.id,
                            ExerciseResult.userinfo_id == self._userinfo_id,
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

    def update_last_user_message_index(self):
        """
        Sets the index of the last user message in the chat.
        """
        self.last_user_message_index = next(
            (
                i
                for i in reversed(range(len(self.messages)))
                if self.messages[i].role == Role.USER.value
            ),
            -1,
        )

    def successfull_submit_message(self):
        """
        show success message if check is passed.
        """
        return rx.toast.success(
            title=BT.successful_submit_title(self.language),
            description=BT.successful_submit_description(self.language),
            duration=2500,
            position="bottom-center",
            invert=True,
        )

    def save_conversation_to_db(self, conversation: list[dict]):
        """
        Saves the conversation to the database.
        """
        if self.current_exercise:
            with rx.session() as session:
                exercise_result = session.exec(
                    select(ExerciseResult).where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == self._userinfo_id,
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
                        userinfo_id=self._userinfo_id,
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

    def get_messages_dict_gpt(self):
        """
        This functions iterates over all previous chat messages and reformats them as a
        list of dictionaries, so they can be handed to the OpenAI-API.
        """
        # Initialize GPT with the desired role, for now GPT acts as a generic tutor.
        # TODO Initialization should change depending on the exercises.
        messages_gpt = [
            {
                "role": Role.SYSTEM.value,
                "content": self.system_message_gpt,
                "check_passed": False,
            }
        ]
        # Iterate through all message, create dictionary for each message and append
        # them to list of dictionaries.
        for chat_message in self.messages:
            messages_gpt.append(
                {
                    "role": chat_message.role,
                    "content": chat_message.message,
                    "check_passed": chat_message.check_passed,
                }
            )
        return messages_gpt

    def load_existing_conversation(self):
        """
        Loads existing conversation from database.
        """
        if self.current_exercise:
            with rx.session() as session:
                exercise_result = session.exec(
                    select(ExerciseResult).where(
                        ExerciseResult.exercise_id == self.current_exercise.id,
                        ExerciseResult.userinfo_id == self._userinfo_id,
                    )
                ).one_or_none()

                if exercise_result:
                    for msg in exercise_result.conversation_text:
                        if msg["role"] != Role.SYSTEM.value:
                            self.append_chat_message(
                                msg["content"],
                                role=Role(msg["role"]),
                                check_passed=msg.get("check_passed", False),
                            )

    def no_exercise_available(self):
        """Sends chat message to user if no exercises are available."""
        self.messages = []
        self.append_chat_message(
            "There are no exercises yet. Please wait till exercises are added.",
            role=Role.AITUTOR,
            check_passed=False,
        )

    def chat_not_available(self):
        """
        Replies to chat message of user if no exercises are available or no
        exercise has been selected. Also prevents unnecessary use of OpenAI API.
        """
        self.append_chat_message(
            message="Chatting is unavailable while no exercises are available "
            + "or no exercise is selected.",
            role=Role.AITUTOR,
            check_passed=False,
        )

    def append_chat_message(
        self,
        message,
        role: Role,
        check_passed: bool,
    ):
        """
        Once a new message is generated by the user it is appended to the list of
        messages in ChatState.
        """
        self.messages.append(
            ChatMessage(
                message=message,
                role=role,
                check_passed=check_passed,
            )
        )
