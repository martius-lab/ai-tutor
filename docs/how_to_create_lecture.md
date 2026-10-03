# Getting started: Creating a new lecture

This guide shows how to

- create a new lecture,
- add members to it, and
- create a first exercise.

/// admonition | Requirements
You need the "lecturer" permission in order to create a new lecture.  If you do not have
that permission yet, please contact the administrators.
///


## Create a new lecture

Go to the "Lectures" page.  This page lists all the lectures you are a member of.  To
create a new lecture, click the "+ Add"-Button on the top right.

If you don't see that button, this means that you don't have the "lecturer" permission,
which is required to create new lectures.  Please contact the administrators in that
case.

Fill out the form:

- **Lecture Name:** Name of the lecture
- **Lecturer:** Name of the person responsible for the lecture (likely you).
- **Registration Code:** A kind of password with which students can join the lecture on
  their own.  The idea is that this code is given to the students in the lecture.  It
  serves as a simple barrier to prevent people from joining, who are not actually
  attending the lecture.  This is optional, **if left empty, everyone can join.**
- **Lecture Information:** Some additional information about the lecture (what is it
  about, etc.).  You can use Markdown for basic formatting.
- **Check Conversation Prompt:** The prompt used for checking if exercises can be
  submitted.  If you just get started, do not worry about this, the default should be
  good.  You can still modify this later, if you want. This field does not need to be changed for **Level AI** exercises.

After submitting the form, you will directly enter the newly added lecture.  If you want
to change any of the information you just entered into the form, you can do so on the
"Settings" tab.


## Managing members

The lecture will now appear in the lecture catalogue, so anyone who knows the
registration code (if you set one) can join on their own.

At the bottom of the "Settings" tab, there is a button "Copy join link".  Use this to
copy a direct link to the lecture to your clipboard.  You can give this link to your
students to make it easier for them to join.  Note that they will still need the
registration code in addition.

You can also manually add members on the "Members" tab (e.g. to directly add
tutors or co-owners of the lecture).  This page also lists all the current members.


### Member roles

You can change the role of each member.  The following roles exist.  They are
hierarchical, so each role also contains the permissions of the roles above in the list.

- STUDENT:  Default role for all users who join a lecture.  Users with this role can work
  on exercises and see other members but nothing else.
- TUTOR:  Can see submissions and reports made by other members as well as the token
  analyzer.
- OWNER:  Can add exercises, edit any settings, manage users, etc.

When creating a new lecture, you automatically join it with the OWNER role.  You can
also make other users OWNER, in which case they will all the same permissions as you.


### Removing members

There are two ways to remove a member from a lecture:

1. Members can leave on their own via the "Leave lecture" button on the "My Lectures"
   page.
2. Lecture owners can remove members via the "kick" button on the "Members" tab of the
   lecture.  Note that they can re-join on their own, if they know the registration
   code, though.


## Creating exercises

To create new exercises, go to the "Manage Exercises" tab of your lecture and click the
"Add Exercise" button.

In **Classic AI**, the students explain the question from the exercise to the AI
agent, which asks questions and provides hints. In **Level AI**, they practise selected topics step
by step, moving from explaining an idea to giving reasons and applying it. Both
types can be used in the same lecture. Title and description are shown to the
students in both modes.

### Prepare a Classic AI exercise

Title and description are shown to the students when they work on the exercise.
The **Lesson context** is hidden from the student but provided to the AI as
additional context. The lecturer can paste relevant excerpts of the lecture script
here or upload a PDF with the context.

The context should be limited to what is actually relevant for the exercise, as
everything included here adds to the token usage when working on the exercise.

**Prompt:** The lecturer can choose a custom prompt for the exercise. A prompt is
an instruction for the AI. For the first exercise, the default is recommended.

### Prepare a Level AI exercise

1. The lecturer uploads one or more PDFs with the relevant lecture material and
   checks the text preview to make sure the content has been read correctly.
2. The lecturer enters a title and an optional description indicating what the
   students should focus on.
3. The lecturer clicks **Generate Concepts**. The AI proposes topics and what the
   students should understand about each one, reducing manual preparation.
4. The lecturer reviews and edits the suggestions before saving:
   - **Concepts** are the topics students will work through.
   - **Core points** are the key ideas their explanations should cover.
   - **Misconceptions** are common misunderstandings the tutor should watch for.
5. The lecturer sets any deadline and tags, then saves the exercise.

For example, for a topic on *correlation and causation*, a key idea could be
"a correlation alone does not show that one factor causes another". A common
misunderstanding could be "if two things occur together, one must cause the other".
The lecturer adapts the wording and examples to the course.

**A small, focused exercise is a suitable starting point.** The lecturer checks
that the suggestions are correct, removes topics outside the scope of the exercise,
and adds anything important that is missing. The requested number of suggestions
is a guide rather than an exact count.

Level AI does not require a custom prompt. The lecturer's main preparation is
reviewing the topics and key ideas that the students will practise.

### Availability and organisation


**Deadline (both modes):** If the lecturer sets a deadline, the students cannot submit
their conversations after it (they can still talk with the AI tutor,
though, e.g. to repeat exercises as exam preparation).
The lecturer also sets the number of days available for working on the exercise.
The exercise will automatically be hidden until the specified
number of days before the deadline.


**Tags (both modes):** Adding tags can help organize exercises. They may be used to
link exercises to specific lectures or to distinguish optional from mandatory exercises.
The lecturer can create tags within the lecture and choose how to use them.

For Level AI, once someone has started a chat, the lecturer can no longer change the
description, source material, or topics and their key ideas. This prevents changing
what students are expected to learn partway through an exercise. The title,
visibility, deadline, working period, and tags can still be changed.
The lecturer reviews the content before the students begin. Trying the exercise
as the lecturer also starts a chat and locks the learning content.


## Working on exercises and reviewing submissions

All members of a lecture can see the exercises in the "Exercises" tab and work on them.

- **Classic AI:** When the student thinks the question of the exercise is explained
  well enough, they can click **Check conversation**. A second AI agent checks the
  conversation and gives feedback on whether the exercise was solved correctly or
  not. If the check passes, the student can submit the conversation.
- **Level AI:** Students work through each topic in three stages: **explain the
  idea**, **give reasons**, and **apply or compare it**. If an explanation leaves
  out an important idea or shows a misunderstanding, the tutor asks a follow-up
  question. Students should answer in their own words; requesting a hint alone
  does not complete a stage. Once all topics are completed, they can submit without
  requesting a separate final check.

In both modes, the student must explicitly submit the conversation. It then appears
in the lecture's **Submissions** tab (visible to owners and tutors) for review.

The submission is a copy of the conversation at the time the student submits it.
Continuing the conversation or starting over does not change that copy. It is only
updated if the student submits again. Unsubmitted conversations are not shown to
lecture tutors or owners in the submission view.
