# Agent Guidance

This repository is shared by humans and coding agents. Other branches or threads may leave unrelated local changes behind. Inspect the real state before acting, then keep your own edits narrow and reviewable.

## Default Workflow

- Work from the user's requested base branch. For new PRs, prefer a branch from `upstream/main` unless the user asks otherwise.
- Read the relevant local context first: `README.md`, `docs/contribute.md`, `docs/architecture.md`, nearby page/state/component files, and related tests.
- Keep diffs surgical. Do not clean up unrelated code, formatting, comments, or dead code unless the current change requires it.
- Prefer small, reviewable PRs. Split independent behavior into follow-up PRs instead of bundling features.
- Do not add speculative fallbacks, mock data, placeholder tests, broad configurability, or unused helpers.
- Avoid making already-large files larger when a focused helper or module is the cleaner local fit. New files should stay small and have one clear responsibility.
- Match the existing Reflex architecture: page folders usually contain `page.py`, `components.py`, and `state.py`; state classes should keep load/logout, computed vars, and action methods easy to scan.
- Handle user-visible failures explicitly. Loading states, errors, and warnings should remain visible long enough to be useful.
- Run the narrowest meaningful verification for the change and report exactly what passed or could not be run.

## Repo-Specific Skills

- For implementation work, read and follow `skills/ai-tutor-implementation/SKILL.md`.
- Before finalizing nontrivial changes, create or use a separate review-only thread and read `skills/ai-tutor-review/SKILL.md`.
- For UI, routing, auth, form, or Reflex state changes, the review thread should run the app and inspect the changed screens when feasible.

## Reviewer Expectations

Reviewers in this repository value small scope, clear code, real behavior checks, and removal of unnecessary code. Common review themes include:

- Prefer database filtering/sorting over Python post-processing when the database can do it clearly.
- Avoid duplicated state that can drift out of sync.
- Be cautious with Reflex state reset, substates, dynamic routing, computed vars, and type-checking limitations.
- Avoid private APIs from dependencies unless there is no reasonable public path and the reason is documented in the PR.
- For Alembic changes, consider both SQLite and PostgreSQL. Existing migrations often need SQLite foreign-key handling when altering tables.
- Keep translations centralized in `aitutor/language_state.py` / `BackendTranslations` when strings are user-visible.
- Remove obsolete states, guards, branches, or tests rather than leaving them for reviewers to find.

## Git And PR Hygiene

- If asked to commit, consider all tracked and untracked changes, then create logical commit groups instead of one large mixed commit.
- Use conventional commit prefixes such as `fix:`, `feat:`, `docs:`, and scoped variants like `fix(auth):`.
- Do not post GitHub comments or mark review threads resolved unless the user asked for that live action.
- When explaining AI-assisted work, be transparent that the human is responsible for the submitted code and comments.
