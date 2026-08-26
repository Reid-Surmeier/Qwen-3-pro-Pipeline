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

