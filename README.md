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

## Partner-compatible local ComfyUI nodes

The local Qwen Image 3 text-to-image and edit nodes expose provider, prompt,
size, count, seed, and provider-capability controls directly in the graph. The
edit node has three ordered, visible reference sockets while retaining Edit
Brief JSON and run metadata for automation and audit.

See [the node and workflow guide](docs/comfyui-partner-nodes.md) and the
[authenticated Mac review procedure](docs/comfyui-mac-review.md). Existing
`QwenImage3Render` JSON workflows remain compatible.
