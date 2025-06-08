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
and this exercise: "{description}"
This is the lesson context uploaded by the teacher as a theoretical basis for this exercise: 

--------------------------
{lesson_context}
--------------------------

The user is a student who has to complete the exercise.
The student will answer the exercise in a conversation with you.
If the student answered the task "{description}" incorrectly, you can give him a hint to help him find the solution.
If the student answered the task "{description}" correctly, you will tell him that he is correct and the task is finished.
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
Check if the answers of the student answered the exercise correctly.
If the student did not answer correctly, respond with what the errors are but do not give the solution.
If the student answered correctly, you can write on sentence that the student answered correctly and the task is finished.
"""
