# Learning by explaining to a chat bot


/// note
This documentation is work in progress.  It does not cover everything yet.
///



## Idea

Students *deepen their understanding of lecture content* by *explaining it to an LLM
chat bot*.  The bot is provided with the lecture material, gives hints and checks the
answers.


## How it works

### Classic AI

The students explain the question from the exercise to the AI agent. The AI then
helps the student to understand the topic by asking questions and providing hints.
Once the student thinks that the exercise is solved, a second AI agent checks the
conversation and gives feedback on whether the exercise was solved correctly or not.

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

### Level AI

Level AI adds a step-by-step approach. The students work through selected topics:
first explaining an idea, then giving reasons, and finally applying or comparing
it. The tutor asks follow-up questions about missing ideas or misunderstandings.
Once all topics and their learning stages are completed, the students can submit
the conversation without requesting a separate final check.

## Choosing an exercise type

Both **Classic AI** and **Level AI** use conversation to help students practise.
The main difference is how the exercise is organised.

| | Classic AI | Level AI |
| --- | --- | --- |
| What do students do? | Explain the question from the exercise to the AI agent. | Work through selected topics in three stages: understand, explain why, and apply or compare. |
| How do they get help? | The tutor asks questions and gives hints during the discussion. | The tutor asks follow-up questions about missing ideas or misunderstandings before moving on. |
| What does the lecturer prepare? | An exercise question and relevant lecture material. | Relevant lecture material, then a review of the topics and key ideas proposed by the AI. |
| When can they submit? | After a second AI agent checks the conversation successfully. | After completing all topics and their learning stages. |



## Example conversations

These screenshots show **Classic AI**.

![Screenshot of an exercise](images/screenshot_chat.png){width=40%}
![Screenshot of an exercise where the user attempts to trick the AI](images/screenshot_chat_check_failed.png){width=40%}
