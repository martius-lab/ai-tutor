# What needs to be in the config.toml file?

# defaultusers
There are 3 default users beeing created in the database. You need to provide the information for each user like this:
```toml
[defaultusers]
# admin information
admin_name = "admin"
admin_password = "1234"
admin_email = "admin@mail.de"

# teacher information
teacher_name = "teacher"
teacher_password = "1234"
teacher_email = "teacher@mail.de"

# student information
student_name = "student"
student_password = "1234"
student_email = "student@mail.de"
```

# prompts
Here you can define the prompts that the admin can choose from when creating a new exercise. you have access to the {title}, {description} and {lesson_file} variables to use in your prompts.
Here is an example of how to define the prompts:
```toml
[prompts]
prompt1 = """
You will act as a learning assistant. The university student is given this exercise-title: "{title}"
and this task-description: "{description}"
This extracted-pdf was uploaded by the teacher as a theoretical basis for this exercise: 

--------------------------
{lesson_file}
--------------------------

Ask the student to explain the task to you. Don't give the student any solutions.
When the student gives you an answer, tell them if it's correct and if they're on the right track.
Your feedback should be brief, in the same language as the student, and should not include any solutions—just hints about what's missing.
"""
prompt2 = """
useless prompt
"""
```

# check-conversation-prompt
Here you define the prompt that should be given to the AI when the check conversation button is pressed.
```toml
[check-conversation-prompt]
prompt = """
"Please check if the answers of the user are serious and if the user answered the original question correctly.
If the user answered the question too short and with too little detail, please ask him to elaborate.
Respond with an explaination of your reasoning.
Your explanation should be in the same language as the user and your explanation should not include any solutions. 
In your explanation you can give hints what is missing in the answer of the user.
If the user did not answer at all, please say that he did not answer.
"""
```