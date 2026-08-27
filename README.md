: This repo is a combination of experiments and test using Comfui and Qwen image pro 3 with Open Ai Codex as a orchestration for the pipeline. 

: Start Date August 20th : 

## Final image output

Completed image sessions are delivered to the
[Agent FigJam board](https://www.figma.com/board/lO1Eo2Xsjnk0HqDPLtOiXT/Agent-FigJam?node-id=0-1)
as untitled, image-only sequential grids. Sessions run top-to-bottom; images
within a session run left-to-right and then top-to-bottom. The pipeline adds no
visible captions, arrows, labels, numbering, or decorative color.

```bash
node .agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs deliver-grid \
  --target agent-final-output-board \
  --run-dir artifacts/runs/SESSION_ID
```

The command uploads every file as a separate FigJam node at its native pixel
dimensions—never as a combined contact sheet. It preserves full images with
`FIT` placement and writes node IDs, hashes, geometry, and readback evidence to
the run-local `figjam-placement.json`. Large sessions use bounded URL-request
chunks without combining or rewriting any source image.

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

## Source-component Assembly

When a Qwen donor has the right large-scale edit but malformed small UI copy or
controls, use the opt-in component Assembly workflow. Its layout JSON names one
raw-donor normalization, one generated clean-plate crop and its destination,
source-owned component crops and their new positions, and the final editable
rectangle:

```bash
python3.12 -m qwen_ui_pipeline component-assembly-workflow layout.json \
  --reference-filename reference.png \
  --generated-filename donor.png \
  --filename-prefix review/component-assembly \
  --preserve-reference-alpha \
  --output component-assembly.api.json
```

The graph uses built-in crop, nearest-exact scale, and hard composite nodes.
It does not send a mask to Qwen or claim to improve the Render Pass itself.
The final region composite restores source-owned pixels outside the declared
edit and, when requested, reconstructs the source alpha exactly. Keep the
original rectangle Assembly for edits that do not need component repair.

Issue-scoped evidence scripts use the optional evidence dependencies:

```bash
python3.12 -m pip install -e '.[evidence]'
python3.12 scripts/build_issue34_component_evidence.py
```
