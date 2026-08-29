# Task

Review branch `{{BRANCH}}` against `{{BASE_BRANCH}}` — the sweep's work on issue #{{ISSUE_NUMBER}} ({{ISSUE_TITLE}}) — and leave it mergeable. You may change the branch; you may not change what it does.

## The diff

!`git diff {{BASE_BRANCH}}...HEAD --stat && git diff {{BASE_BRANCH}}...HEAD | head -c 120000`

## The commits

!`git log --oneline {{BASE_BRANCH}}..HEAD`

## The issue

!`gh issue view {{ISSUE_NUMBER}} 2>/dev/null | head -c 20000 || echo "(gh could not read the issue)"`

## Verification, as run by the sweep after the implementer

```
{{VERIFY_OUTPUT}}
```

## What to check

1. **Spec**: does the change do what the issue asks — all of it, and nothing else? Missing acceptance criteria are defects.
2. **Standards**: `.sandcastle/CODING_STANDARDS.md`, `AGENTS.md`, and the ADRs under `docs/adr/`. A frozen interface, error type, or acceptance test changed without an Issue saying so is a defect.
3. **Correctness**: edge cases, error handling as values, tests that assert behaviour rather than implementation.
4. **Safety**: no secret values, no injection, no destructive commands.
5. **Clarity**: names, nesting, dead code.

## What to do

- Fix defects directly on the branch and commit with messages prefixed `SWEEP: review:`.
- Re-run `{{VERIFY_COMMANDS}}` and make it pass.
- If the branch is already clean, change nothing.
- Never push, never open or edit a PR, never close the issue, never change labels.

When done, output exactly:

<promise>COMPLETE</promise>
