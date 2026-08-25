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
- paid operations, credentials, and human approvals are identified,
- the human has approved the final work packet.

Use `needs-info` when an unanswered question could materially change the solution. Use `needs-human-decision` after an agent has proposed a complete triage brief and a human must approve, revise, split, or reject it. Use `ready-for-human` when direct human judgment or execution—not approval of an agent plan—is required.

## Conversational triage gate

While an Issue has `needs-triage`, an agent may investigate and comment but must not create a branch or modify repository files. The comment uses this structure:

```markdown
## Agent triage brief

### 1. Interpretation

### 2. Open decisions

### 3. Proposed scope

### 4. Proposed acceptance and verification

### 5. Recommendation
```

The recommendation is one of: proceed, revise, split, investigate first, or do not pursue. After commenting, the agent replaces `needs-triage` with `needs-human-decision` and stops.

The human then approves, revises, splits, or rejects the proposal. Silence, an unaddressed comment, or the absence of objections is not approval. Only the human may authorize `ready-for-agent`.

After approval, update the Issue body with the final outcome, scope, acceptance criteria, verification, dependencies, and approvals. Comments remain the decision history; the Issue body becomes the canonical implementation specification.

## Linking work

Name branches descriptively and link the Issue in the pull request. Use a closing keyword when the pull request fully resolves the Issue:

```text
Closes #<issue-number>
```

If a pull request discovers additional work, create a follow-up Issue instead of expanding the current branch without review.

## Comments and decisions

Use Issue comments for investigation findings, reproduction evidence, and scope clarification. Durable architectural decisions belong in an ADR; link the ADR from the Issue and pull request.

See [`repository-workflow.md`](repository-workflow.md) for the complete lifecycle and [`triage-labels.md`](triage-labels.md) for canonical status labels.
