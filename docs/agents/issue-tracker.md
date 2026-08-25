# Issue tracker: GitHub Issues

GitHub Issues are the authoritative work tracker for `Qwen-3-Pro-Pipeline`.

Local Markdown notes may be used for temporary thinking, but they are not authoritative and must not silently replace or contradict the GitHub Issue. The previous `.scratch/` tracker is historical migration material unless a future ADR deliberately restores a local-first workflow.

## Issue types

Use Issues for:

- bugs and regressions,
- features and behavior changes,
- investigations and experiments,
- documentation tasks,
- CI and repository-management tasks,
- maintenance chores.

## Required content

An Issue should contain the smallest amount of information needed to make the outcome testable:

```markdown
## Problem or desired outcome

## Evidence or current behavior

## Expected behavior

## Acceptance criteria

## In scope

## Out of scope

## Verification

## Dependencies and approvals
```

Do not prescribe implementation details unless they are already constrained by an accepted ADR or interface contract.

## Readiness

An Issue can receive `ready-for-agent` only when:

- the outcome is unambiguous,
- acceptance criteria are observable,
- scope boundaries are stated,
- dependencies are available,
- verification is possible,
- paid operations, credentials, and human approvals are identified.

Use `needs-info` when an unanswered question could materially change the solution. Use `ready-for-human` when direct human judgment or execution is required.

## Linking work

Name branches descriptively and link the Issue in the pull request. Use a closing keyword when the pull request fully resolves the Issue:

```text
Closes #<issue-number>
```

If a pull request discovers additional work, create a follow-up Issue instead of expanding the current branch without review.

## Comments and decisions

Use Issue comments for investigation findings, reproduction evidence, and scope clarification. Durable architectural decisions belong in an ADR; link the ADR from the Issue and pull request.

See [`repository-workflow.md`](repository-workflow.md) for the complete lifecycle and [`triage-labels.md`](triage-labels.md) for canonical status labels.
