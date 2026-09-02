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
  good.  You can still modify this later, if you want.

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

- STUDENT:  Default role for all uses who join a lecture.  Users with this role can work
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

Title and description will be shown to the students when they work on the exercise.  The
"Lesson context" is hidden from the student but provided to the LLM as additional
context.  You can, for example, paste relevant excerpts of your lecture script here.
Alternatively, you can upload a PDF with the context.
**Please limit the context to what is actually relevant for the exercise as everything
included here will add to the token usage when working on the exercise.**

**Prompt:** You can choose a custom prompt for the exercise.  If you are just getting
started, we recommend, that you stick to the default, though.


**Deadline:** If you set a deadline for the exercise, student will not be able to submit
their conversations anymore after the deadline (they can still talk with the AI tutor,
though, e.g. to repeat exercises as exam preparation).
When setting a deadline, you also have to set a period of days, the students have to
work on the exercise.  The exercise will automatically be hidden until the specified
number of days before the deadline.


**Tags:** Adding tags can help organizing exercises.  They may be used, for example, to
link exercises to specific lectures or to distinguish optional from mandatory exercises.
You can add arbitrary tags within your lecture, so it is up to you, how you use them.


## Working on exercises and reviewing submissions

All members of a lecture can see the exercises in the "Exercises" tab and work on them.
When a user thinks, the question of the exercise is explained well enough, they can
click the "Check conversation" button.  This will trigger a call to an LLM, checking the
conversation.  If the check passes, the user can submit the conversation.  The submitted
conversation will appear in the "Submissions" tab of the lecture (visible to owners and
tutors), where it can be reviewed.

The user may continue the conversation (or even resetting and starting over) but this
will not affect the submitted snapshot.  The submitted conversation is only updated if
the user explicitly submits again.  Unsubmitted conversations are not visible to other
users, also not to tutors or owners.
