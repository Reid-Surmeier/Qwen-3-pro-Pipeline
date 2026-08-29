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

## Release train and the integration line (owner directive, 2026-08-27)

The owner reviews **versions, not fragments**. Main is not the review surface:

- The standing integration line is the `release/v0.2.0` branch and its PR
  (#82). It merges to `main` only when the owner declares the final version
  done; no agent merges it.
- Do not present individual feature/test PRs to the owner for review. Land
  work by merging your branch into the current integration line (resolve
  conflicts there, then run the full baseline on the integrated tree). A
  fragment PR may exist briefly for CI, but park it as a draft with a pointer
  to the release PR once folded in.
- The release PR body is the changelog: every folded change gets a line, a
  steward review verdict, and — for anything visual — embedded evidence.
  Non-blocking review findings are collected into a follow-up issue, never
  dropped.
- Direct pushes to `main` are limited to what the owner explicitly names
  (this procedure section itself was one such push).

### Current milestone: Godot Interactive Replica

The repository's end goal is reverse-engineering the RO-style Japanese HUD
Reference Screen (`artifacts/references/ro-hud-fullscreen/` on the
integration line) into a living Godot 4.7.2 replica (`godot/` directory):
every window draggable, text live, checkboxes and buttons functional, with
animations mimicking or referenced exactly from the source. The Figma Design
componentization layer is retired; FigJam remains reference intake only. The
extraction, fidelity-contract, palette, and vision-verifier machinery of the
integration line is validated by being used for this — treat gaps found
while building as defects to fix on the line, not reasons to bypass it.

The replica must be **self-verifying**: headless import, engine contract
tests, rendered-frame fidelity checks, and error capture that produces
machine-readable reports an agent can consume and course-correct from,
without the owner relaying errors by hand. Multiple testing rounds are
required before anything is called engineered.

### Paid generation for this milestone run

The owner set a cap of **200 Qwen generations** for the current milestone
run (2026-08-27), superseding ADR 0003's per-issue ceiling for work on this
milestone only. Everything else in ADR 0003 stands: explicit OpenRouter
only, smallest useful batch, pre-submission records before spending, full
provenance, ambiguous requests counted as spent and never blindly retried,
no paid execution in ordinary CI. Maintain the running count in
`artifacts/references/ro-hud-fullscreen/generation-ledger.json` on the
integration line; stop before any request that could exceed 200.

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

## Blind artifact-review gate

A pull request that creates or changes visual or interactive output additionally requires an independent blind artifact review before human approval. The blind reviewer runs in a fresh context and receives only the review packet — acceptance contract, hash-locked references, candidate artifact, exact candidate SHA, and launch/reset instructions — and judges the artifact, not the implementer's account of it.

- The implementation agent applies `ready-for-blind-review` only when the packet at `artifacts/reviews/issue-<n>/packet.json` passes `scripts/validate_blind_review_packet.py` against the candidate SHA.
- Only the blind reviewer applies `blind-review-passed`, `blind-review-failed`, or `blind-review-blocked`; every verdict names its SHA, and a new commit invalidates it.
- The reviewer posts reproducible findings with expected behavior, actual behavior, evidence, and the violated contract clause; it never modifies the candidate.
- Blind review is advisory evidence for the owner's final visual approval, not a substitute for it.

Full procedure, packet schema, label rules, and the review template: [`docs/agents/blind-review.md`](docs/agents/blind-review.md).

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
