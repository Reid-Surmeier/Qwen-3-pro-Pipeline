# Task

Implement issue #{{ISSUE_NUMBER}} — {{ISSUE_TITLE}} — on branch `{{BRANCH}}` (based on `{{BASE_BRANCH}}`).

This is cycle {{ATTEMPT}} of at most {{MAX_ATTEMPTS}} the hourly sweep will spend on this issue. Finish the work; a cycle that ends without the completion signal is continued next hour from your commits, and after {{MAX_ATTEMPTS}} unfinished cycles a person takes over.

## The issue, in full

!`gh issue view {{ISSUE_NUMBER}} --comments 2>/dev/null || echo "(gh could not read the issue; work from the title)"`

## What this branch already holds (your earlier cycles)

!`git log --oneline {{BASE_BRANCH}}..HEAD 2>/dev/null || git log --oneline -10`

## Rules of this repository

Read these before changing anything, in this order:

1. `AGENTS.md` (and `CLAUDE.md` if present) — the operating contract.
2. `CONTEXT.md` — the vocabulary; use it, never the words it says to avoid.
3. `MODULES.md` if present, then the `MODULE.md` of every module the issue names.
4. `docs/adr/` — decisions you may not reverse.
5. `.sandcastle/CODING_STANDARDS.md` — what the reviewer will enforce.

Skills: {{SKILLS_NOTE}}

## How to work

1. Explore before editing: read the relevant source and tests.
2. Where a test seam exists, red → green → refactor. Do not invent new seams to make something testable.
3. Keep the change as small as the issue allows. One issue, nothing else.
4. Before every commit run: `{{VERIFY_COMMANDS}}` — and fix what fails.
5. Commit on `{{BRANCH}}` with conventional messages prefixed `SWEEP:` (e.g. `SWEEP: feat: …`). Commit as you go; uncommitted work is lost.

## Never

- push, open or edit a PR, close the issue, or change labels — the sweep does those;
- write a secret value anywhere; `.env` files are not yours to create;
- touch files outside what the issue needs;
- leave TODOs or commented-out code in a commit.

## When you are done

When the issue's acceptance criteria are met, `{{VERIFY_COMMANDS}}` passes, and everything is committed, output exactly:

<promise>COMPLETE</promise>

If you are blocked (a decision only the owner can make, a missing credential, a failing check you cannot fix), commit what is safe, write one comment-style paragraph starting with `BLOCKED:` explaining what you need, and stop without the signal.
