# Triage labels

These labels describe whether work is ready and who should act next. They are
workflow gates, not priority labels. Human approval happens at the pull
request, not on the Issue
([ADR 0007](../adr/0007-move-human-approval-to-the-pull-request-gate.md)).

| Label | Meaning | Exit condition |
| --- | --- | --- |
| `needs-triage` | The Issue has not been analyzed yet. | An agent or maintainer posts a triage brief, sharpens the Issue body, and either proceeds or applies `needs-info`/`blocked`. |
| `needs-info` | A material question the agent cannot answer from the repository, primary sources, or bounded experimentation blocks safe implementation. | The missing information is added and acceptance criteria are testable. |
| `blocked` | Work is specified but cannot begin until a named dependency is complete. | The named dependency's observable completion event occurs; readiness is then re-evaluated (removal does not imply readiness by itself). |
| `ready-for-agent` | Descriptive: the Issue is well-specified and an agent can pick it up without further sharpening. | An isolated branch/worktree is created and work begins. |
| `ready-for-human` | Direct human judgment or execution is required (an action only the human can take, such as an external account step). | The human action is recorded. |
| `wontfix` | The work will not be actioned. | The reason is documented and the Issue is closed. |

`needs-human-decision` is retired. Existing Issues carrying it should be
treated as ordinary triaged Issues: an agent may proceed, and the human vetoes
or redirects at the pull request.

## `blocked` requirements

A blocked Issue must:

- name at least one concrete dependency with `Blocked by #N` (or a native
  dependency link),
- state the observable event that permits reassessment (for example: "the
  dependency's PR merges to `main`").

While `blocked` is present, agents must not create an implementation branch or
begin code for the Issue. Removing `blocked` triggers re-evaluation of the
Issue's readiness; it does not automatically make the Issue `ready-for-agent`.

Example: Issue #1 was blocked by Issue #17 — Issue #1 carried `blocked` with a
comment naming Issue #17, and became actionable for re-evaluation when Issue
#17's qualification run completed. The specific numbers are an example, not an
architectural assumption.

## Readiness checklist

An Issue is ready for implementation when it has:

- a clear problem or desired outcome,
- observable acceptance criteria,
- explicit in-scope and out-of-scope boundaries,
- a named verification method,
- known dependencies (none of them open under `blocked`).

If something on this list is missing, the agent sharpens the Issue body first
and states the interpretation it takes; the human can veto that interpretation
at the PR gate. Paid OpenRouter generation for Issue testing is generally
authorized within ADR 0003's bounds and needs no per-Issue approval.

Priority, type, and subsystem labels may be added separately; they do not
replace readiness state.
