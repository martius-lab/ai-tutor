# What needs to be in the config.toml file?

# default_users

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
role = "teacher"
name = "teacher"
password = "1234"
email = "teacher@mail.de"

[[default_users]]
role = "student"
name = "student"
password = "1234"
email = "student@mail.de"
```

# exercise_prompts

Here you can define the prompts that the admin can choose from when creating a new
exercise. you have access to the {title}, {description} and {lesson_context} variables to
use in your prompts.

Here is an example of how to define the prompts:
```toml
[[exercise_prompts]]
name = "prompt 1"
prompt = """
You will act as a learning assistant. The university student is given this exercise-title: "{title}"
and this task-description: "{description}"
This extracted-pdf was uploaded by the teacher as a theoretical basis for this exercise: 

--------------------------
{lesson_context}
--------------------------

Ask the student to explain the task to you. Don't give the student any solutions.
When the student gives you an answer, tell them if it's correct and if they're on the right track.
Your feedback should be brief, in the same language as the student, and should not include any solutions—just hints about what's missing.
"""

[[exercise_prompts]]
name = "prompt 2"
prompt = """
useless prompt
"""
```

# check_conversation_prompt

Here you define the prompt that should be given to the AI when the check conversation
button is pressed.
```toml
[check_conversation_prompt]
prompt = """
"Please check if the answers of the user are serious and if the user answered the original question correctly.
If the user answered the question too short and with too little detail, please ask him to elaborate.
Respond with an explaination of your reasoning.
Your explanation should be in the same language as the user and your explanation should not include any solutions. 
In your explanation you can give hints what is missing in the answer of the user.
If the user did not answer at all, please say that he did not answer.
"""
```
