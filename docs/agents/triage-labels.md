# Triage labels

These labels describe whether work is ready and who should act next. They are workflow gates, not priority labels.

| Label | Meaning | Exit condition |
| --- | --- | --- |
| `needs-triage` | Maintainer or agent analysis is required; implementation is forbidden. | An agent posts a triage brief and moves the Issue to `needs-human-decision`, or a maintainer chooses another state. |
| `needs-info` | A material question blocks safe implementation. | The missing information is added and acceptance criteria are testable. |
| `needs-human-decision` | Agent triage is complete; a human must approve, revise, split, or reject it. | The human records a decision and either authorizes `ready-for-agent`, requests changes, or closes/splits the Issue. |
| `ready-for-agent` | The Issue body contains the human-approved implementation specification. | An isolated branch/worktree is created and work begins. |
| `ready-for-human` | Direct human judgment or execution is required; this is not the agent-plan approval state. | The human decision/action is recorded. |
| `wontfix` | The work will not be actioned. | The reason is documented and the Issue is closed. |

## `ready-for-agent` checklist

Apply `ready-for-agent` only when the Issue has:

- a clear problem or desired outcome,
- observable acceptance criteria,
- explicit in-scope and out-of-scope boundaries,
- a named verification method,
- known dependencies,
- explicit approval boundaries for credentials, external systems, paid calls, or subjective visual decisions.

If an agent would need to guess about product intent, architecture, security, cost, or acceptance, the Issue is not ready.

Priority, type, and subsystem labels may be added separately; they do not replace readiness state.
