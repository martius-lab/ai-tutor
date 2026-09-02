# Learning by explaining to a chat bot


/// note
This documentation is work in progress.  It does not cover everything yet.
///



## Idea

Students *deepen their understanding of lecture content* by *explaining it to an LLM
chat bot*.  The bot is provided with the lecture material, gives hints and checks the
answers.


## How it works

1. **Setup:** The lecturer creates exercises and provides context from the lecture
   material (e.g.  slides, script, ...).
2. **Explain:** The student explains the exercise question to the AI tutor in their own
   words.
3. **Guided dialogue:** The AI tutor asks questions and gives hints — it never reveals
   the solution directly.
4. **Check the answer:** A separate agent reviews the whole conversation.
5. **Submit & review:** On a successful check the student submits the chat.  Tutors read
   submissions for evaluation.



## Key features

- **Based on lecture material:** Exercises use lecture material as context.
- **Two-agent design:** A guiding tutor plus an independent checker for evaluation.
- **Large Language Model:** GPT-4.1(-mini) by OpenAI.
- **Review by humans:** Human tutors can review the submitted conversations.
- **Token monitoring:** Lecturers can monitor token usage per exercise/user and set limit.
- **Multi-language UI:** German and English.


## Example Conversations

![Screenshot of an exercise](images/screenshot_chat.png){width=40%}
![Screenshot of an exercise where the user attempts to trick the AI](images/screenshot_chat_check_failed.png){width=40%}
