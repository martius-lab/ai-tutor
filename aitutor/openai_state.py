"""OpenAI Interface for requests and answers (with chat log)"""

import os
from openai import AsyncOpenAI
import reflex as rx


class OpenAIState(rx.State):
    """Manages OpenAI state"""

    # current input from user
    user_input: str

    # chat log as tuple (user_input, OpenAI-answer)
    chat_history: list[tuple[str, str]]

    async def answer(self):
        """Sends asynchron requests to OpenAI and
        processes answer in realtime.
        """
        client = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
        )

        # send async request to OpenAI
        # answer will be streamed and therefore received in fragments
        session = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": self.user_input}],
            stop=None,
            temperature=0.7,
            stream=True,
        )

        # start with empty answer and initialize chat history
        answer = ""
        self.chat_history.append((self.user_input, answer))

        # clear user input and frontend input
        self.user_input = ""
        yield

        # iterate over streamed answer
        async for item in session:
            # check if current fragment has content
            if hasattr(item.choices[0].delta, "content"):
                # "None" indicates end of the response
                if item.choices[0].delta.content is None:
                    break

                # add current answer fragment to answer var
                answer += item.choices[0].delta.content
                # update last log message with answer fragment
                self.chat_history[-1] = (
                    self.chat_history[-1][0],
                    answer,
                )
                yield
