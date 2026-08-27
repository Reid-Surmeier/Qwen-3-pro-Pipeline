# Matt Pocock skills in this repository

This repository vendors the project-local skill set selected in GitHub Issue #30. The installed `SKILL.md` files are procedures available to compatible coding agents; they are not permissions to bypass the active Issue, repository verification, review, or human image-quality gates.

## Invocation syntax

The command syntax depends on the agent hosting the skill:

| Runtime | Explicit invocation |
| --- | --- |
| Codex CLI or IDE | Run `/skills` to browse, or type `$to-spec` to mention the skill |
| Claude Code | Type `/to-spec` when the project skill is exposed as a slash command |
| Hermes | Ask naturally: `Use the to-spec skill`; Hermes slash commands are app commands, not arbitrary project-skill names |

Codex scans `.agents/skills` from the working directory up to the repository root. Start Codex inside this repository. If a newly installed skill is not listed, start a fresh session before diagnosing the files.

For a discovery check, use a fresh interactive Codex session: `/skills` must list the catalog, and typing `$to-spec` must open the mention picker. When the same skill is also installed for the user, select the entry whose detail path begins with this repository's `.agents/skills/`. A non-interactive `codex exec` prompt does not exercise the interactive catalog and is not discovery evidence.

## The engineering chain

```text
conversation and repository context
  -> to-spec
  -> one GitHub Issue containing the approved specification
  -> to-tickets, only when the work benefits from independent slices
  -> implement on the current unblocked ticket
  -> code-review against an exact committed fixed point
  -> pull request, CI, human review, merge
```

`grill-with-docs` may precede `to-spec` when product or architectural decisions are unresolved. `tdd`, `diagnosing-bugs`, `domain-modeling`, and `codebase-design` are supporting disciplines that other workflows may invoke when relevant.

## How ticketing works here

A **specification** describes the whole approved outcome: user value, decisions, test seams, scope, and exclusions. In this repository, a specification normally lives in the body of its authoritative GitHub Issue.

A **ticket** is one independently verifiable unit of implementation. GitHub calls that record an **Issue**. A small specification can be implemented through the same Issue; it does not need artificial child tickets.

For larger work, `to-tickets` creates tracer-bullet Issues and records their blocker relationships. A ticket is on the **frontier** when every Issue blocking it is complete. Only frontier tickets carrying `ready-for-agent` may be implemented.

```text
Parent specification
  ├── Ticket A — no blockers; current frontier
  ├── Ticket B — blocked by A
  └── Ticket C — blocked by A and B
```

Branches and commits are implementation history, not tickets. The pull request connects that history back to the ticket with `Closes #<issue-number>` when merging fully resolves it.

## Repository-specific authority

The existing project documents override conflicting upstream defaults:

- GitHub Issues are authoritative: see `docs/agents/issue-tracker.md`.
- The six-state conversational gate is authoritative: see `docs/agents/triage-labels.md`.
- The repository uses one root domain context: see `docs/agents/domain.md` and `CONTEXT.md`.
- Architecture decisions remain under `docs/adr/`.
- `AGENTS.md` remains the operating contract for implementation, verification, commits, PRs, and human approvals.

The upstream `to-spec` procedure asks to apply `ready-for-agent` directly. Here that is valid only when the human has explicitly approved the final work packet. Otherwise, follow the conversational triage gate instead.

## Review cautions

`code-review` compares `<fixed-point>...HEAD`, so it excludes staged and uncommitted work. Commit the candidate change before review and supply an exact fixed point rather than asking the skill to guess.

- Run consequential review in a fresh session when practical.
- Keep Standards and Spec findings separate; one axis must not hide failure on the other.
- Treat sub-agent findings as hypotheses and verify every cited location.
- Do not rerun review indefinitely in search of a permanently clean subjective result.
- Review sub-agents must not invoke `code-review` or spawn additional review agents recursively.

The local skill name may collide with a host's built-in `/code-review`. In Codex, select the project skill explicitly with `$code-review`. Do not remove a built-in skill merely to resolve the naming collision.

## Installation and updates

`skills-lock.json` records every installed source path and computed content hash. `skills-provenance.json` records the installer version, resolved upstream commit, scope, and selected inventory.

Audit the checked-in inventory without reading or changing user-global agent directories:

```bash
python3.12 scripts/audit_project_skills.py
```

The audit requires exactly 37 provenance and lock entries, readable canonical `SKILL.md` files, the required engineering-chain skills, and project-contained Claude compatibility links. The pre-existing `figma-qwen-ui-pipeline` skill remains a separate repository-owned skill and is not counted as part of the upstream 37.

Updates are deliberate repository changes:

```bash
npx -y skills@1.5.23 update --project --yes
```

Run updates only on an Issue-linked branch or worktree. Review the source revision, every skill diff, lockfile changes, security signals, and agent compatibility links before committing. Never enable unattended upstream updates.

The complete set includes stable, general, miscellaneous, and in-progress skills because the user explicitly selected all 37 discovered entries. Presence does not imply relevance: invoke a skill only when its description matches the current task.
