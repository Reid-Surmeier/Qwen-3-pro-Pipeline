# Move human approval to the pull-request gate

Status: accepted on 2026-08-26 (owner decision recorded in a live session).

Issue-level human approval is retired. Issues remain the authoritative
statement of a problem, its acceptance criteria, and its scope, but agents no
longer wait for a human decision on an Issue before creating a branch,
implementing, or running bounded paid verification. The pull request is the
single human approval gate: nothing merges without human review, and every
subjective visual decision, paid-spend reconciliation, credential concern, or
production effect is approved or rejected there.

Consequences for the Issue lifecycle:

- `needs-human-decision` is retired as a blocking state. Triage briefs are
  still welcome as the first comment, but they do not pause work.
- `ready-for-agent` becomes descriptive rather than a required permission.
  An agent may proceed once the Issue states an outcome, testable acceptance
  criteria, and scope boundaries; if those are missing, the agent improves the
  Issue body first, then proceeds.
- `needs-info` and `blocked` still pause work: the first marks a material
  unanswered question, the second a named unfinished dependency.
- The PR gate is unchanged and strengthened: linked Issue, verification
  results, visual evidence, spend records, limitations, and required human
  approvals all land in the PR, and a human merge decision is final.

Consequences for paid generation:

- OpenRouter paid image generation for Issue testing is generally authorized
  and no longer requires per-Issue human pre-approval.
- Everything else in ADR 0003 stands: explicit OpenRouter only, smallest
  useful batch, the 10-cumulative-output ceiling per linked Issue/PR, full
  provenance records, ambiguous requests counted as spent and never blindly
  retried, and no paid or model-backed execution in ordinary pull-request CI.
- Pre-submission records (question, batch, estimate, stop rule) are still
  written before spending — as an Issue comment or committed note — because
  they are the evidence the PR reviewer audits.

This supersedes the issue-level approval language in earlier documents where
they conflict; ADR 0003's spending bounds are not changed by this record.
