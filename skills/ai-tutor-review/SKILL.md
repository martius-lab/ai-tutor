---
name: ai-tutor-review
description: Review ai-tutor changes before finalizing a PR. Use after implementation to inspect diffs, find dead code and scope creep, run targeted checks, and perform browser/screenshot validation for UI, routing, auth, form, or Reflex state changes.
---

# AI Tutor Review

## Overview

Use this skill in a review-only pass after implementation. The goal is to catch the issues that have repeatedly made ai-tutor PRs harder to review: oversized scope, dead code, duplicated state, weak tests, Reflex runtime surprises, and UI behavior that was not exercised.

## Review Mode Rules

- Start from `git status --short --branch` and `git diff --stat`.
- Review only the implementation diff unless the user explicitly expands scope.
- Do not make broad cleanup edits. If fixes are needed, keep them targeted to findings from the review.
- Lead the final review output with findings, ordered by severity, with file and line references.
- If there are no findings, say so and state residual risks or unverified paths.

## Diff Review Checklist

- Scope: Does the diff include independent features or cleanup that should be split out?
- Dead code: Are there unused helpers, obsolete branches, redundant config values, old tests, or duplicate state fields?
- Reflex state: Can reset/logout behavior clear data that should persist, or leave sensitive/user-specific state behind?
- Dependency APIs: Does the change call private methods or rely on undocumented Reflex behavior without a reason?
- Data flow: Can a duplicated ID/value drift from the route or database source of truth?
- Database: Are filtering, sorting, joins, and uniqueness handled in the database when appropriate?
- Migrations: Are SQLite and PostgreSQL both considered, especially foreign keys, constraints, and boolean defaults?
- Translations: Are user-visible strings centralized in the existing language system?
- Errors: Are failures logged or displayed clearly, and do warnings stay visible long enough to read?
- Tests: Do tests exercise behavior rather than implementation text, and are they scoped to the change?

## Runtime And Screenshot Review

Use this section when the diff changes UI, routing, auth protection, forms, upload flows, loading/error states, Reflex state behavior, or generated frontend output.

- Run the app with `uv run reflex run` unless the environment lacks required secrets or setup.
- Open the changed screen in a browser.
- Exercise the changed interaction, including the main failure path when feasible.
- Capture screenshots of the changed screen or flow.
- Check browser console and terminal output for Reflex/runtime errors.
- Look for flicker, invisible loading, unreadable warnings, broken hover/dialog nesting, clipped text, and inconsistent desktop/mobile behavior.
- Report which screens and interactions were checked. Do not claim full E2E coverage from a narrow smoke test.

## Targeted Commands

Pick the smallest meaningful set for the diff:

- `uv run ruff check <changed files>`
- `uv run pyright <changed files or aitutor>`
- `uv run pytest <relevant tests>`
- `uv run reflex run`
- `git diff --check`

If a command cannot run, record the exact reason and what review coverage remains.

## Reviewer Pattern Reminders

- Smaller PRs are easier to review; recommend splitting when the diff mixes concerns.
- Simpler code is preferred over clever local state, private API calls, and broad guards.
- Reflex behavior should be tested in the app when the change depends on generated frontend/runtime behavior.
- Database migrations need extra care because production may use PostgreSQL while local development often uses SQLite.
- If AI-generated code left an obvious quirk, naming inconsistency, or redundant path, call it out before the human reviewer has to.
