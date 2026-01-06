# Configuration File
The config file is only used to initialize the application by setting the configuration values in the database. This makes the first time setup faster.
If no config.toml file is found, the default config is used for initialization. Changes can be made in the admin interface later on.

# What needs to be in the config.toml file?
## check_conversation_prompt

Here you define the prompt that should be given to the AI when the check conversation
button is pressed.
```toml
check_conversation_prompt = """
Check if the answers of the student answered the exercise correctly.
If the student did not answer correctly, respond with what the errors are but do not give the solution.
If the student answered correctly, you can write one sentence that the student answered correctly and the task is finished.
"""
```

## ai models

You can define which ai model should be used for the normal responses and which for the check conversation responses. To see which models you can use, please refer to the open ai [documentation](https://platform.openai.com/docs/models).

```toml
response_ai_model = "gpt-4.1-mini"

check_ai_model = "gpt-4.1"
```

## info text on the home page
The homepage has 3 sections to display your information.
- One section to explain how to use the ai tutor
- One section with general information
- One section with specific information about the lecture

These information texts can be set in the configfile and get rendered in markdown format.
They are **optional**. If you don't want to use one of them. Just set them to: `""`


```toml
how_to_use_text = """
I am your AI tutor and I want to help you understand the content of the lecture. Here's how it works:

1. Explain to me the question I ask you at the beginning of the conversation.
2. When you think the question has been answered – and I also confirm that it has been answered – you can use the "Check Answer" button to verify the conversation. A separate AI will then check whether the task was solved correctly. If the check is successful, you can submit the chat history.

I’m looking forward to working with you!
"""
general_information_text = """
- The AI tutor should only be used for working on the tasks.
- Tutors and professors can view chats that have been submitted.
"""
lecture_information_text = """
# Lecture: Example Lecture XY
- Lecturer: Prof. Dr. Max Mustermann
- Contact: max.mustermann@uni-tuebingen.de
- Content: This lecture is intended to provide an understanding of basic methods and concepts of XY.
"""
```

The lecture title also gets displayed. You can set it in the variable `course_name`. This is mandatory.

```toml
course_name = "Example Lecture XY"
```

## Impressum
On the Impressum page, this text will be displayed in markdown format.
It has to contain information for who is responsible for the contents of the webiste.
```toml
impressum_text = "This is the impressum text."
```

## Registration Code
To prevent random people from registering an account and burning the api tokens, you have to define a registration code. New users must type in this code when registering their account.
```toml
registration_code = "exampleCode1234"
```


## default_users

You can define a number of default users, that are automatically created.  This is
intended to make testing easier.
**Default users are only created if no user with the given role exists yet!**

```toml
[[default_users]]
role = "admin"
name = "admin"
password = "1234"
email = "admin@mail.de"

[[default_users]]
role = "tutor"
name = "tutor"
password = "1234"
email = "tutor@mail.de"

[[default_users]]
role = "student"
name = "student"
password = "1234"
email = "student@mail.de"
```

## exercise_prompts

Here you can define the prompts that the admin can choose from when creating a new
exercise. you have access to the `{title}`, `{description}` and `{lesson_context}` variables to
use in your prompts.
The first prompt you define will be the default prompt ("prompt 1" in the example below). This prompt will be selected if the admin does not specifically select another one when creating an exercise.

Here is an example of how to define the prompts:
```toml
[[exercise_prompts]]
name = "prompt 1"
prompt = """
You will act as a learning assistant. The university student is given this exercise-title: "{title}"
and this exercise: "{description}"
This is the lesson context uploaded by the teacher as a theoretical basis for this exercise: 

--------------------------
{lesson_context}
--------------------------

The user is a student who has to complete the exercise.
The student will answer the exercise in a conversation with you.
If the student answered the task "{description}" incorrectly, you can give him a hint to help him find the solution but do **not** tell him the solution.
If the student answered the task "{description}" correctly, you will tell him that he is correct and the task is finished.
Do not engage in any other topics than the exercise at hand. If the student asks anything unrelated, tell him that you are only here to help with the exercise.
"""

[[exercise_prompts]]
name = "prompt 2"
prompt = """
useless prompt
"""
```

