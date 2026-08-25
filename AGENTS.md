# Agent operating contract

This file defines how coding agents must work in this repository. It does not replace project meaning in [`CONTEXT.md`](CONTEXT.md), architectural rationale in [`docs/adr/`](docs/adr/), or the acceptance criteria in the active GitHub Issue.

## Authority and required reading

Before changing files, read in this order:

1. The active GitHub Issue and its acceptance criteria.
2. This `AGENTS.md` file.
3. [`CONTEXT.md`](CONTEXT.md) for canonical vocabulary and relationships.
4. Applicable records in [`docs/adr/`](docs/adr/).
5. The nearest domain, package, test, or workflow documentation relevant to the change.

If these sources conflict, stop and surface the conflict. Do not silently choose one interpretation or rewrite an accepted ADR.

## Work-readiness gate

Implementation may begin only when:

- one authoritative GitHub Issue identifies the problem or desired outcome,
- the Issue has testable acceptance criteria,
- in-scope and out-of-scope boundaries are clear,
- the expected verification method is named,
- dependencies and human approvals are identified,
- the Issue is labeled `ready-for-agent`.

If a material requirement is missing, return the Issue to `needs-info`. Do not fill product or architectural gaps by guessing.

## Preflight

Before editing:

```bash
git status --short --branch
git diff --check
```

Then confirm:

- the current branch or worktree belongs to the active Issue,
- unrelated working-tree changes will not be included,
- no secret or credential is present in the requested inputs,
- the proposed work does not conflict with `CONTEXT.md` or an accepted ADR,
- paid generation or external side effects have the required human approval.

A failed preflight is a stop condition.

## Branch and worktree rules

- Treat `main` as the known-good shared baseline.
- Do not implement directly on `main`.
- Use one branch or worktree for one coherent goal.
- Use descriptive prefixes: `docs/`, `feat/`, `fix/`, `refactor/`, `test/`, or `ci/`.
- Keep historical snapshots and WIP archives separate from active development branches.
- Do not discard, overwrite, stage, or commit unrelated user work.
- Do not mix opportunistic cleanup into the requested change.

## Change discipline

- Make the smallest change that satisfies the Issue.
- Preserve current behavior unless the Issue explicitly changes it.
- Do not reorganize or rewrite the codebase merely to make it look cleaner.
- For behavior changes, establish a failing test or other observable failure before implementing the fix when practical.
- Update documentation when public behavior, terminology, configuration, or operational procedure changes.
- Create or supersede an ADR when a decision changes system boundaries, sources of truth, security, cost, data flow, or long-term implementation direction.

## Domain guardrails

- Treat the Reference Screen as authoritative input.
- Record source identity and SHA-256 when a workflow claims source locking.
- Distinguish probabilistic Render Passes from deterministic Assembly.
- Do not call generated output authoritative before required human approval.
- Strict preservation requires a Fidelity Check, including zero changed pixels outside declared edit regions when exact preservation is claimed.
- Use exact baseline and candidate commit SHAs for reproducible comparisons.
- Do not place provider keys, tokens, passwords, or credentials in source, logs, prompts, issues, pull requests, workflow YAML, or artifacts.
- Paid or model-backed evaluation must not run automatically in ordinary pull-request CI.
- Do not blindly retry an ambiguous provider failure that might create duplicate billing.

## Verification gate

Run focused checks while developing, then run the repository baseline before requesting review:

```bash
python3.12 -m unittest discover -s tests -v
node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs
python3.12 -m compileall -q qwen_ui_pipeline tests scripts
git diff --check
```

If the change affects JavaScript tooling, ComfyUI integration, deployment, or artifacts, run the relevant additional checks and record them in the pull request.

Do not describe work as verified unless the commands were actually run and their results are reported. Pre-existing failures must be distinguished from failures introduced by the change.

## Commit gate

- Stage specific intended files; do not use `git add -A` in a dirty worktree.
- Keep each commit coherent and recoverable.
- Prefer Conventional Commit subjects such as `docs:`, `fix:`, `feat:`, `test:`, `refactor:`, or `ci:`.
- Never invent or overwrite Git author identity. If `user.name` or `user.email` is missing, stop and let the human configure it.
- Do not commit credentials, temporary outputs, unclassified large artifacts, or unrelated files.

## Pull-request gate

A pull request must include:

- a linked authoritative Issue,
- a concise summary of the change,
- explicit in-scope and out-of-scope boundaries,
- verification commands and real results,
- artifact or visual evidence when relevant,
- risks, limitations, and follow-up work,
- any human approvals still required.

Review the pull request twice:

1. **Specification review** — does it satisfy the Issue and acceptance criteria?
2. **Engineering review** — is it safe, minimal, understandable, tested, and consistent with the architecture?

Do not merge until required deterministic checks pass and the human has approved any subjective visual decision, paid execution, credential use, or production effect.

## Artifact policy

Classify generated material before adding it:

- source reference,
- approved output,
- comparison evidence,
- reproducibility metadata,
- rejected candidate,
- temporary scratch output.

Choose ordinary Git, Git LFS, release assets, or an external artifact store deliberately. Preserve manifests and hashes when files live outside Git. Never delete historical artifacts as incidental cleanup.

## Stop conditions

Stop and ask for human direction when:

- requirements or acceptance criteria are ambiguous,
- a requested change conflicts with an accepted ADR,
- credentials or sensitive information appear in the worktree,
- paid generation or an external side effect lacks approval,
- exact preservation cannot be objectively verified,
- the requested action would overwrite unrelated work,
- Git author identity is missing at commit time,
- the verification result is incomplete or contradictory.

See [`docs/agents/repository-workflow.md`](docs/agents/repository-workflow.md) for the complete lifecycle.
