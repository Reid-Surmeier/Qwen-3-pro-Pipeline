: This repo is a combination of experiments and test using Comfui and Qwen image pro 3 with Open Ai Codex as a orchestration for the pipeline. 

: Start Date August 20th : 

## Memory-safe worker capacity

Use the dry-run capacity planner before changing the number of ComfyUI workers.
It combines a recent, sanitized host-memory snapshot with explicit reserve and
queue assumptions; it does not start workers, submit jobs, or call a provider.

```bash
qwen-worker-capacity \
  --input artifacts/benchmarks/comfyui-capacity-issue-24/request.json \
  --output artifacts/benchmarks/comfyui-capacity-issue-24/result.json
```

The command fails closed when the memory evidence is stale or contradictory.
Treat `increase-workers` as a planning result, not deployment authorization:
active-job memory peaks and provider concurrency still require separate
validation before changing the worker service.

## Opt-in mask-aware Assembly

Issue #2 adds deterministic ComfyUI nodes and workflow builders for removing a
rectangular background under an explicit ownership mask. This path does not
replace Qwen Image 3 Pro or the existing rectangular Assembly workflow.

The mask workflow keeps the Reference Screen immutable outside the approved
mask and fails closed when protected pixels or approved artwork drift. The
Assembly graph reuses the approved mask, so it does not claim an independent
candidate-silhouette check; shifted-mask geometry is tested separately. See
[`docs/research/comfyui-mask-node-qualification.md`](docs/research/comfyui-mask-node-qualification.md)
for live schemas, tests, alternatives, and the bounded six-output comparison.
