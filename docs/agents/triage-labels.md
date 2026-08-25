# Triage labels

These labels describe whether work is ready and who should act next. They are workflow gates, not priority labels.

| Label | Meaning | Exit condition |
| --- | --- | --- |
| `needs-triage` | Maintainer evaluation is required. | Scope and next owner are identified. |
| `needs-info` | A material question blocks safe implementation. | The missing information is added and acceptance criteria are testable. |
| `ready-for-agent` | The Issue is fully specified for agent implementation. | An isolated branch/worktree is created and work begins. |
| `ready-for-human` | Human judgment or direct human execution is required. | The human decision/action is recorded. |
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
