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

While an Issue is labeled `needs-triage`, an agent may inspect relevant context and post a triage brief, but must not create a branch, edit repository files, or begin implementation. The brief must cover interpretation, material open decisions, proposed scope, proposed acceptance/verification, and a recommendation.

After posting the brief, replace `needs-triage` with `needs-human-decision`. While that label is present, wait for the human to approve, revise, split, or reject the proposal. Silence is not approval. Only a human may authorize the transition from `needs-human-decision` to `ready-for-agent`.

Before applying `ready-for-agent`, update the Issue body so the approved specification—not the comment thread—is the canonical work packet.

Implementation may begin only when:

- one authoritative GitHub Issue identifies the problem or desired outcome,
- the Issue body contains the human-approved specification,
- the Issue has testable acceptance criteria,
- in-scope and out-of-scope boundaries are clear,
- the expected verification method is named,
- dependencies and human approvals are identified,
- neither `needs-triage`, `needs-info`, nor `needs-human-decision` is present,
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

### Current milestone: the reusable screenshot → Interactive Replica system

The repository's end goal is a **reusable system** that turns a screenshot of a
windowed pixel UI into an Interactive Replica in Godot 4.7.2 — not a single
replica. A new Reference Screen brings a new manifest and new assets; it must not
bring new engine code. The work is charted on **wayfinder map #103**, and the
proving case is the second RO desktop (`artifacts/references/ro-desktop-b/`,
FigJam board `wbOhmbJkG83vj2NMgfnQr2` node `1:5`, native 1536×1024, 11 windows,
239 controls), run through the whole pipeline from the beginning.

Start from the map, not from memory: read #103, take the first open, unblocked,
unassigned child ticket, assign it to yourself before doing any work, and resolve
one per session (research tickets excepted).

The previous milestone — the `ro-hud-fullscreen` replica in `godot/` — was judged
poorly tested by the owner and is superseded (#102). Do not build on it.

### Aliveness: every control has a State Set

A Reference Screen shows each control in exactly **one** state. Every interactive
element owns a full **State Set** — idle, hover, pressed, settled/active, and
disabled where the Source Game has one — so the missing states must be inventoried
per control and produced in the same style, then integrated so that hovering and
pressing visibly change the control. A control that is a region of a flat picture
with an invisible hit rectangle over it is **not** implemented.

Transitions are **instant**. Every transition measured in the Source Game completes
in one frame at 30–60 fps (#115); its entire UI layer contains no animation.
Aliveness here means an immediate state swap, not easing. Adding tweening makes the
replica less faithful, not more.

Hover states are added **in the same style everywhere**, including where the Source
Game has none. Any such addition is marked `invented-in-style` on the Behaviour Card
so the owner can strike it. Pressed, checked and selected states are always
source-exact.

### The Source Game is the behaviour authority

Before a control is built, its behaviour comes from real footage and screenshots of
the Source Game, recorded as a **Behaviour Card**: gesture → expected visible
response, timing in frames, reversibility, whether the source shows a hover state,
and the evidence (URL, timestamp, fps, crop) under
`artifacts/references/<game>/behaviour/`. The owner confirms cards; agents never
author behaviour from imagination and present it as observed.

Two traps, both paid for once:

- **An edit cut is indistinguishable from an instant UI response.** Tutorial footage
  cuts every few seconds. Verify every timing claim with a cut detector — a per-frame
  diff over a region containing no UI — before believing it.
- **Below ~30 fps a drag and a burst of discrete steps look identical.** Re-read any
  apparent ramp at native frame rate before calling it continuous motion.

Where the Source Game is silent, say so on the card and specify from intent in the
open. Never present an intent-specified gesture as observed.

### Verification: the Playtester, not a reviewer

Judgement of an Interactive Replica comes from a **Playtester** — an agent that
drives the running artifact through real input events and produces its own evidence.
An agent that grades evidence the builder produced is not a verification step; that
design passed byte-identical before/after frames on 2026-08-27.

- Two Playtesters play **independently and blind to each other**; either one finding
  a dead or wrong control fails the run. Because Claude Code builds, the Codex
  session's play is the verdict that counts.
- Blindness is a **fresh session on a packet directory** — a `git archive` at the
  candidate SHA with no `.git`, no backlog, no PR text, no host memory or rules —
  with browser and screenshot tools only. Verified invocations are in
  `docs/research/blind-playtester-sessions/`.
- The verdict is **computed from the Play Log**, never asserted by the Playtester.
  Any `responsive: no` on a catalogued control fails. Any catalogued control not
  exercised makes the run INCOMPLETE — never a pass.
- The quality floor and its twelve gates are **ADR 0006**. Mechanical metrics are
  regression backstops; they never constitute a pass.

### Build unit: one window at a time, one release per screen

One GitHub Issue per window (a **Window Issue**); a window ships only when its Play
Log is green; every window folds into **one release pull request per Reference
Screen**. The owner reviews versions, never fragments.

### Paid generation

Missing States are produced by deterministic derivation wherever the Source Game's
own rendering is a known transform, and by a Qwen Asset Pass otherwise. Every output
— derived or generated — is reviewed at ≥4× magnification and regenerated when it is
not acceptable.

The owner set a cap of **300 Qwen generations** for the current Reference Screen
(2026-08-29), superseding ADR 0003's per-issue ceiling for this milestone only.
Everything else in ADR 0003 stands: explicit OpenRouter only, smallest useful batch,
pre-submission records before spending, full provenance, ambiguous requests counted
as spent and never blindly retried, no paid execution in ordinary CI. Maintain the
running count in the generation ledger beside the Reference Screen; stop before any
request that could exceed 300.

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
- Issue-scoped paid verification may use OpenRouter only. Use the smallest useful batch, never exceed 10 cumulative output images for the linked Issue/PR, and stop before submitting any request that could produce image 11. Do not use `provider: auto` or direct Alibaba under this allowance.
- Record requested and completed image counts, provider/model, prompt or task ID, estimate and actual cost when exposed, output paths, hashes, and provenance for every paid verification run.
- Do not blindly retry an ambiguous provider failure that might create duplicate billing.
- Count an ambiguous possibly billed request against the 10-image verification allowance until it is reconciled.

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

For a change to an Interactive Replica, this baseline is **not** the gate. The gate
is a green Play Log from a blind Playtester run under ADR 0006 — the commands above
are regression backstops beneath it. A replica change reported as verified on the
strength of the baseline alone is reported wrongly.

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
