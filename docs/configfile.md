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
You will act as a learning assistant. The university student is given this exercise-title: - {title} -
and this task-description: - {description} -
This extracted-pdf was uploaded by the teacher as a theoretical basis for this exercise: - {lesson_file} -
Analyze the answers of the student and give feedback.
"""
prompt2 = """
useless prompt
"""
```

# check-answer-prompts
Here you define the prompt that should be given to the AI when the check answer button is pressed.
```toml
[check-answer-prompt]
prompt = """
"Please check if the answer is correct and provide an explanation."
"""
```