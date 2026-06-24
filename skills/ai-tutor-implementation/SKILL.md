---
name: ai-tutor-implementation
description: Implement focused changes in the ai-tutor repository. Use when adding or modifying Python, Reflex UI/state, authentication, configuration, database models, Alembic migrations, tests, documentation, or other behavior in this repo.
---

# AI Tutor Implementation

## Overview

Use this skill to make repo-native changes that match the expectations shown in prior ai-tutor reviews: small scope, clear Reflex state boundaries, visible error handling, meaningful tests, and no dead or speculative code.

## Start With Context

- Confirm the current branch and dirty worktree before editing. Ignore unrelated changes unless they block the task.
- Read the files that define the local pattern before changing code. For page work, inspect the relevant `page.py`, `components.py`, `state.py`, and nearby tests.
- Read `docs/architecture.md` before adding pages, state classes, routes, or database-backed behavior.
- Check recent PR/reviewer context when the task follows up on GitHub review comments.

## Keep Scope Reviewable

- Implement the smallest complete change that satisfies the request.
- Split independent features, large flows, or cleanup into follow-up PRs instead of bundling them.
- Do not add placeholder UI, mock data, speculative fallbacks, unused config, or tests that only check for strings unless that string output is the real contract.
- Remove code made obsolete by your change. Do not leave duplicate paths for reviewers to find.
- Prefer focused modules over growing files that are already hard to scan. If touching a large file, keep the edit local and consider extracting new behavior into a small helper file.

## Reflex And State

- Preserve the page folder pattern: `page.py` for route/page composition, `components.py` for UI helpers, and `state.py` for event and data logic.
- Keep state values minimal. Avoid duplicating route IDs, database values, or derived flags that can drift out of sync.
- Add new user-specific state to logout/reset handling when needed. Do not reset session-independent preferences, such as language, by accident.
- Prefer public APIs from Reflex and `reflex-local-auth`. If a private method is unavoidable, keep the call isolated and explain why in the PR.
- Computed vars that touch database-backed state may need explicit initial values for frontend builds.
- Expect pyright and Reflex to disagree sometimes. Use `# type: ignore` only when the runtime behavior is verified and a clearer typed structure is not practical.

## Data And Configuration

- Let the database filter, sort, and join data when that is clearer and avoids Python-side drift.
- Validate inputs at the boundary where users or config write values. Avoid repeated defensive correction when reading already-validated config.
- Keep user-visible strings in the existing translation system, usually `aitutor/language_state.py` or `BackendTranslations`.
- For settings, preserve actual deployment behavior. `.env` is read from the process working directory; production and Docker paths may differ from source-file-relative paths.
- For OpenAI-compatible providers, treat normal chat and structured-output checks as separate compatibility surfaces.

## Database Migrations

- Generate migrations with `uv run reflex db makemigrations` when possible, then inspect the result.
- Consider both SQLite and PostgreSQL. SQLite table alteration can recreate tables and may need foreign-key handling as seen in existing Alembic scripts.
- Use PostgreSQL-compatible defaults for booleans and constraints where relevant.
- Do not include migrations for unrelated model changes.

## Verification

- Run the narrowest meaningful command for the touched code.
- Common checks include:
  - `uv run ruff check <changed files>`
  - `uv run pyright <changed files or package>` when the change affects typed backend logic
  - `uv run pytest <relevant test files or test names>`
  - `uv run reflex run` for interactive UI/runtime validation
- Report exactly which checks passed and which were skipped.
- After implementation, use `skills/ai-tutor-review/SKILL.md` in a separate review-only thread before finalizing substantial changes.
