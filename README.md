# Qwen-3-Pro-Pipeline

A reference-preserving image-generation pipeline built around **Qwen Image 3 Pro**, **ComfyUI**, provider APIs, and deterministic region assembly.

The project turns a structured edit description into a controlled render, records the inputs and outputs needed to reproduce the run, and preserves authoritative pixels outside explicitly approved edit regions.

> **Status:** This repository is being reorganized from a preserved project snapshot. The first migration work is documentation, repository structure, and agentic-coding workflow—not a rewrite of the image pipeline.

## Purpose

The pipeline is designed for controlled image editing rather than unconstrained full-screen redrawing.

It separates two different kinds of work:

1. **Probabilistic generation** — Qwen proposes a donor image or isolated asset.
2. **Deterministic assembly** — application code or a controlled ComfyUI graph places the approved result into the authoritative reference.

That separation matters because a model can produce a visually plausible image without preserving every unrelated pixel, exact string, or layout relationship.

## Pipeline at a glance

```text
Reference Screen
      |
      v
Edit Brief
      |
      v
Compile controlled instructions
      |
      v
Render Pass through a provider or ComfyUI
      |
      v
Candidate batch and provenance record
      |
      v
Human donor approval
      |
      v
Deterministic region Assembly
      |
      v
Fidelity Check
      |
      v
Approved output / Interactive Replica work
```

### Core concepts

- **Reference Screen** — the source image whose composition and relationships are authoritative.
- **Edit Brief** — a structured description of the intended change.
- **Preservation Invariant** — a relationship that must remain unchanged.
- **Exact Copy** — text that must appear verbatim.
- **Render Pass** — one model invocation with fixed inputs and a fixed seed.
- **Asset Pass** — a focused render for one reusable interface element.
- **Screen Pass** — a render for a composed interface view.
- **Assembly** — placement of approved assets and exact copy into the source composition.
- **Fidelity Check** — comparison against the reference and its preservation invariants.
- **Interactive Replica** — a working software view derived from an approved composition.

The project vocabulary and relationships are defined in [`CONTEXT.md`](CONTEXT.md).

## Architecture and guardrails

The central architectural rule is:

> **Qwen may propose pixels; deterministic assembly decides which pixels become authoritative.**

The current design therefore expects the following boundaries:

- The source reference is preserved and, where required, checksum-verified.
- The intended change is represented as an Edit Brief rather than an unstructured request blob.
- Provider/model/profile choices are recorded as part of run provenance.
- A generated donor is not authoritative merely because it looks good.
- Assembly happens only after the donor or asset is approved.
- Strict preservation is measured outside the declared edit region; visual similarity alone is not proof of pixel identity.
- Provider failures must not be retried in ways that could create duplicate billing when the result is ambiguous.
- Credentials are injected through the environment or an external secret manager; they are not stored in this repository.

The architectural rationale is recorded in:

- [`docs/adr/0001-separate-rendering-from-assembly.md`](docs/adr/0001-separate-rendering-from-assembly.md)
- [`docs/adr/0002-preserve-immutable-pixels-with-region-assembly.md`](docs/adr/0002-preserve-immutable-pixels-with-region-assembly.md)

## Repository map

| Path | Responsibility |
| --- | --- |
| `qwen_ui_pipeline/` | Python package, CLI, prompt compilation, workflow generation, provider routing, and run recording |
| `qwen_ui_pipeline/providers/` | OpenRouter, Alibaba, and provider-routing clients |
| `comfyui_custom_nodes/` | ComfyUI custom-node integration |
| `schemas/` | Structured Edit Brief schemas |
| `examples/` | Small example briefs used for inspection and workflow generation |
| `workflows/` | Generated ComfyUI API workflow examples |
| `tests/` | Python and integration-oriented tests |
| `scripts/` | Experiment and run orchestration scripts |
| `artifacts/` | Preserved references, run records, images, and historical evidence |
| `deploy/` | Sanitized host/service setup material; never credentials |
| `docs/adr/` | Durable architectural decisions and their rationale |
| `docs/agents/` | Agent and repository-management guidance |
| `docs/research/` | Prompting and external research notes |
| `docs/runs/` | Evaluated experiment records |
| `.agents/skills/` | Project-local reusable agent procedures |
| `AGENTS.md` | Agent operating contract and pointers to detailed rules |
| `CONTEXT.md` | Domain vocabulary, relationships, and invariants |

## Installation

The package requires Python 3.12 or newer.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Provider credentials are runtime inputs. Use the machine's approved secret-injection mechanism to provide environment variables such as:

```text
OPENROUTER_API_KEY
DASHSCOPE_API_KEY
```

Never commit, print, or place credentials in source files, workflow files, prompts, artifacts, issues, or pull requests.

## CLI entry point

The package exposes the `qwen-ui-pipeline` command. The module form is also supported:

```bash
python -m qwen_ui_pipeline <command> ...
```

The main commands are:

### Compile an Edit Brief

```bash
python -m qwen_ui_pipeline compile \
  examples/golf-club-object-v002.json \
  --json
```

### Generate a ComfyUI API workflow

```bash
python -m qwen_ui_pipeline workflow \
  examples/golf-club-object-v002.json \
  --reference-filename plantstudio-main-window.gif \
  --filename-prefix golf-ui/club-preview/v002 \
  --output workflows/golf-club-object-v002.api.json
```

### Generate a deterministic assembly workflow

```bash
python -m qwen_ui_pipeline assembly-workflow \
  --reference-filename plantstudio-main-window.png \
  --generated-filename golf-club-v002-2.png \
  --region 182,78,37,165 \
  --filename-prefix golf-ui/club-assembly/v003 \
  --output workflows/golf-club-assembly-v003.api.json
```

### Record completed ComfyUI outputs

`record-comfy` records a completed output and its request/provenance information without pretending that the CLI itself performed the render.

```bash
python -m qwen_ui_pipeline record-comfy \
  examples/golf-club-object-v002.json \
  --provider alibaba \
  --reference artifacts/references/plantstudio-main-window.png \
  --image path/to/completed-output.png \
  --output-dir artifacts/runs/example-run \
  --prompt-id prompt-id-from-the-run
```

## Verification

Use the repository's current deterministic checks before opening a pull request:

```bash
python -m unittest discover -s tests -v
node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs
python -m compileall -q qwen_ui_pipeline tests scripts
git diff --check
```

The snapshot does not currently claim a GitHub Actions workflow. The first planned workflow is a cheap pull-request verification job that runs the same tests and compilation checks. Full provider-backed image generation should remain separate until its infrastructure, cost controls, credentials, reproducibility, and human-approval boundaries are defined.

## Reproducibility and evidence

A useful run should preserve enough information to answer:

- Which source reference was used?
- What was its SHA-256 hash?
- Which Edit Brief and compiled prompt were used?
- Which provider, model, workflow profile, and seed were used?
- Which candidates were generated?
- Which candidate was approved?
- Which region was assembled?
- What did the Fidelity Check measure?

Generated images are not the only evidence. Run manifests, requests, responses, workflow graphs, selection records, and comparison metrics are part of the provenance story.

Large generated artifacts require deliberate classification. Before adding new output, decide whether it belongs in ordinary Git, Git LFS, a release asset, or an external artifact store with a manifest and hashes. Do not turn every temporary render into active source material.

## Agentic repository workflow

The repository is managed as a sequence of explicit gates:

```text
Issue
  -> triage
  -> ready-for-agent
  -> isolated branch or worktree
  -> implementation
  -> local verification
  -> pull request
  -> CI and review
  -> approval
  -> merge to main
```

### Issues

An Issue should explain the problem or desired outcome, evidence, constraints, and acceptance criteria. It should not prescribe an implementation unless the implementation is already a deliberate decision.

An Issue is ready for an agent only when the goal, boundaries, expected behavior, and verification method are clear enough to act without guessing.

### Branches and worktrees

- Keep `main` as the known-good shared baseline.
- Use one branch or worktree per coherent goal.
- Prefer names such as `docs/...`, `feat/...`, `fix/...`, `refactor/...`, and `ci/...`.
- Do not mix unrelated cleanup into a feature branch.
- Preserve historical snapshots and work-in-progress archives separately from the active development line.

### Commits

A commit should be a small, coherent, recoverable checkpoint. Prefer Conventional Commit-style subjects:

```text
docs: explain source-locked generation
ci: add deterministic pull-request verification
refactor: isolate provider routing
fix: reject assembly outside the declared region
```

Do not commit credentials, unreviewed generated output, or unrelated working-tree material merely because it is present.

### Pull requests

A pull request should make review easy. It should include:

- the Issue or learning goal it addresses,
- a short summary of the change,
- files or boundaries intentionally changed,
- verification commands and their results,
- artifact or visual evidence when relevant,
- known limitations and follow-up work.

Review has two separate questions:

1. **Specification review:** Does the change solve the Issue and satisfy its acceptance criteria?
2. **Engineering review:** Is the change safe, understandable, maintainable, and consistent with the architecture?

## GitHub Actions policy

Actions are for repeatable repository automation. They are not a replacement for architectural judgment or human visual approval.

The default CI path should be:

- cheap,
- deterministic,
- safe on a standard hosted runner,
- free of provider credentials and paid model calls.

A later visual-evaluation workflow may run against exact baseline and candidate commit SHAs and upload manifests, images, diffs, and metrics. It should be separately triggered and should place paid generation and subjective acceptance behind explicit human approval.

## What is intentionally not automated yet

The following boundaries remain deliberate:

- A model's visual output is not automatically accepted as final.
- Paid provider generation is not part of ordinary pull-request CI.
- A model is not the authority for exact text, layout, or immutable pixels.
- A failed or ambiguous provider request is not blindly retried.
- A large historical artifact collection is not automatically reorganized or deleted.

## Further reading

- [`AGENTS.md`](AGENTS.md) — current agent guidance
- [`CONTEXT.md`](CONTEXT.md) — project vocabulary and invariants
- [`docs/adr/`](docs/adr/) — architectural decisions
- [`docs/agents/`](docs/agents/) — agent and triage guidance
- [`docs/research/`](docs/research/) — prompting research
- [`docs/runs/`](docs/runs/) — evaluated experiment records
- [`deploy/README.md`](deploy/README.md) — sanitized runtime setup notes
