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

Human approval lives at the pull request, not the Issue
([ADR 0004](docs/adr/0004-move-human-approval-to-the-pull-request-gate.md)).
An agent may triage an Issue and proceed directly to implementation without
waiting for an Issue-level human decision.

Implementation may begin only when:

- one authoritative GitHub Issue identifies the problem or desired outcome,
- the Issue has testable acceptance criteria,
- in-scope and out-of-scope boundaries are clear,
- the expected verification method is named,
- neither `needs-info` nor `blocked` is present.

If the Issue body is missing one of those, sharpen the body first (a triage
brief comment plus a body update), then proceed. Use `needs-info` only for a
material question the agent genuinely cannot answer from the repository,
primary sources, or bounded experimentation. Do not fill product or
architectural gaps by silent guessing — state the interpretation taken in the
Issue and the pull request so the human can veto it at the PR gate.

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
- paid generation stays within the standing OpenRouter allowance (ADR 0003,
  ADR 0004) and external side effects beyond it have human approval.

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
- Paid image generation for Issue testing is generally authorized through explicit OpenRouter only (ADR 0004); it needs no per-Issue human pre-approval. Use the smallest useful batch, never exceed 10 cumulative output images for the linked Issue/PR, and stop before submitting any request that could produce image 11. Do not use `provider: auto` or direct Alibaba under this allowance. Write the pre-submission record (question, batch, estimate, stop rule) before spending.
- Record requested and completed image counts, provider/model, prompt or task ID, estimate and actual cost when exposed, output paths, hashes, and provenance for every paid verification run.
- Do not blindly retry an ambiguous provider failure that might create duplicate billing.
- Count an ambiguous possibly billed request against the 10-image verification allowance until it is reconciled.

## Verification gate

Run focused checks while developing, then run the canonical repository
baseline before requesting review:

```bash
scripts/verify.sh
```

The script runs the Python unit tests, Node tests, Python compilation, and
`git diff --check`, fails non-zero when any check fails, and is the same
entry point GitHub Actions invokes. Do not maintain a separate command list.

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
- paid generation would exceed the standing allowance, or an external side effect beyond it lacks approval,
- exact preservation cannot be objectively verified,
- the requested action would overwrite unrelated work,
- Git author identity is missing at commit time,
- the verification result is incomplete or contradictory.

See [`docs/agents/repository-workflow.md`](docs/agents/repository-workflow.md) for the complete lifecycle.
