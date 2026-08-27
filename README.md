# Qwen-3-Pro-Pipeline

A reference-preserving UI image pipeline: it transforms an existing interface
image with **Qwen Image 3 Pro** while keeping the source's visual identity,
then deterministically assembles approved pixels into deliverable artifacts.
ComfyUI hosts the execution graph; explicit provider adapters call OpenRouter
or Alibaba; every run leaves hashes, costs, and provenance behind.

Core vocabulary (Reference Screen, Edit Brief, Render Pass, Assembly,
Fidelity Check, Exact Copy) is defined in [`CONTEXT.md`](CONTEXT.md) and used
consistently across issues, code, and reviews.

## The two halves of every run

1. **Render Pass (probabilistic)** — one image-model invocation with a fixed
   Edit Brief, references, and seed. Its output is a *candidate*, never
   authoritative.
2. **Assembly (deterministic)** — approved pixels are composited into the
   Reference Screen under declared regions, and a Fidelity Check proves zero
   changed pixels outside those regions when exact preservation is claimed.

Keeping these separate is the repository's central architectural rule; see
[`docs/adr/0001-separate-rendering-from-assembly.md`](docs/adr/0001-separate-rendering-from-assembly.md)
and
[`docs/adr/0002-preserve-immutable-pixels-with-region-assembly.md`](docs/adr/0002-preserve-immutable-pixels-with-region-assembly.md).

## Repository map

| Path | Contents |
| --- | --- |
| [`qwen_ui_pipeline/`](qwen_ui_pipeline/) | Python package: Edit Brief compiler, provider adapters (OpenRouter/Alibaba), ComfyUI node and workflow builders, capacity planner |
| [`comfyui_custom_nodes/`](comfyui_custom_nodes/) | ComfyUI registration wrapper for the local Qwen nodes |
| [`workflows/`](workflows/) | Saved ComfyUI API workflow JSON |
| [`schemas/`](schemas/) | Versioned machine-readable contracts |
| [`scripts/`](scripts/) | Benchmarks and repository tooling |
| [`tests/`](tests/) | Python `unittest` suites and Node tests |
| [`artifacts/`](artifacts/) | References, run outputs, benchmarks, and evidence (classified per the artifact policy in [`AGENTS.md`](AGENTS.md)) |
| [`docs/adr/`](docs/adr/) | Accepted architectural decision records |
| [`docs/agents/`](docs/agents/) | Issue lifecycle, labels, and workflow documentation |
| [`docs/research/`](docs/research/) | Primary-source research notes |
| [`deploy/`](deploy/) | systemd service and MCP configuration for the ComfyUI host |

## CLI

The package installs a `qwen-ui-pipeline` entry point (also available as
`python3.12 -m qwen_ui_pipeline`):

```text
qwen-ui-pipeline compile             # compile an Edit Brief
qwen-ui-pipeline generate            # run a provider-routed Render Pass
qwen-ui-pipeline workflow            # write a ComfyUI API workflow
qwen-ui-pipeline assembly-workflow   # write a deterministic region-assembly workflow
qwen-ui-pipeline component-workflow  # write a lossless component-extraction workflow
qwen-ui-pipeline record-comfy        # record completed ComfyUI outputs as a run
```

A separate `qwen-worker-capacity` command plans memory-safe ComfyUI worker
counts from a sanitized host-memory snapshot; it never starts workers or calls
a provider:

```bash
qwen-worker-capacity \
  --input artifacts/benchmarks/comfyui-capacity-issue-24/request.json \
  --output artifacts/benchmarks/comfyui-capacity-issue-24/result.json
```

It fails closed when the memory evidence is stale or contradictory. Treat
`increase-workers` as a planning result, not deployment authorization.

## Local verification

Python 3.12 and Node are the supported environment:

```bash
python3.12 -m unittest discover -s tests -v
node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs
python3.12 -m compileall -q qwen_ui_pipeline tests scripts
git diff --check
```

## Credentials and paid generation

- Provider keys are injected into the ComfyUI worker environment at service
  start; they never appear in source, prompts, issues, pull requests,
  workflow YAML, or artifacts.
- Paid verification is bounded by
  [`docs/adr/0003-bound-paid-verification-to-openrouter.md`](docs/adr/0003-bound-paid-verification-to-openrouter.md):
  explicit OpenRouter only, smallest useful batch, at most 10 cumulative
  outputs per linked Issue/PR, full provenance for every run, and no paid or
  model-backed execution in ordinary pull-request CI.
- Ambiguous possibly-billed requests count as spent and are never blindly
  retried.

## Final image output

Completed image sessions are delivered to the
[Agent FigJam board](https://www.figma.com/board/lO1Eo2Xsjnk0HqDPLtOiXT/Agent-FigJam?node-id=0-1)
as untitled, image-only sequential grids:

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs deliver-grid \
  --target agent-final-output-board \
  --run-dir artifacts/runs/SESSION_ID
```

Each file uploads as a separate FigJam node at native pixel dimensions, with
node IDs, hashes, geometry, and readback evidence written to the run-local
`figjam-placement.json`.

## How work happens here

GitHub Issues are the authoritative tracker; agents implement on isolated
branches/worktrees and every change lands through a reviewed pull request.
The operating contract for agents — readiness gates, verification, commit and
PR requirements, artifact policy — lives in [`AGENTS.md`](AGENTS.md), with the
full lifecycle in
[`docs/agents/repository-workflow.md`](docs/agents/repository-workflow.md).
