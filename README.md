# Qwen UI pipeline

A reference-preserving UI workflow built around Qwen Image 3 Pro, ComfyUI,
Figma/FigJam, and deterministic application code.

## Current machine setup

- ComfyUI `0.31.0` runs as the enabled user service `qwen-comfyui.service`.
- The local UI/API is `http://10.255.255.254:8188` on this WSL host.
- `Qwen Image 3 Render` calls the provider API without exposing keys in a
  workflow.
- `Reference Region Composite` restores the immutable reference outside an
  explicit `x,y,width,height` region.
- `comfyui-mcp` `0.50.98` is registered as the `comfyui` Codex MCP server.
- OpenRouter and Alibaba keys are injected from Bitwarden Secrets Manager by
  the service wrapper; they are not stored in this repository.

Sanitized copies of the service unit, secret-injection wrapper, and Codex MCP
registration live in [`deploy/`](deploy/README.md) so the host setup can be
recreated without copying credentials.

Check the service and API:

```bash
systemctl --user status qwen-comfyui.service
curl -fsS http://10.255.255.254:8188/system_stats
```

The MCP registration becomes available automatically in a new Codex session.
No ComfyUI API key is required while the service remains bound to the local WSL
loopback alias.

## Pipeline

1. Preserve a Reference Screen and checksum it.
2. Describe one controlled change as an Edit Brief.
3. Compile the brief into ordered instruction blocks within Qwen Image 3's
   approximate 4.5K-token image-instruction budget.
4. Run a fixed-seed Render Pass through ComfyUI.
5. Compare the batch and retain provenance for the selected output.
6. For strict preservation, composite only the approved region onto a
   lossless PNG reference.
7. Upload contact sheets and approved outputs to FigJam without replacing the
   source.
8. Rebuild labels, layout, controls, and animation as native Figma and web
   elements.

Production image generation is fail-closed under workflow profile
`qwen-source-locked-single-decision-v1`. The profile requires Alibaba Qwen Image
3 Pro through ComfyUI, one bounded visual decision, an immutable source hash, an
explicit source-ratio size, four fixed-seed candidates, and an approval gate
before deterministic assembly. Built-in OpenAI image generation and direct
provider execution are not production paths in this repository.

Preflight the source, workflow, provider, decision count, candidate batch, seed,
and prompt budget before compiling or rendering:

```bash
python3 -m qwen_ui_pipeline preflight \
  examples/golf-club-object-v002.json \
  --reference artifacts/references/plantstudio-main-window.gif
```

Compile and inspect a brief:

```bash
python3 -m qwen_ui_pipeline compile examples/golf-club-object-v002.json --json
```

Generate the ComfyUI API graph:

```bash
python3 -m qwen_ui_pipeline workflow \
  examples/golf-club-object-v002.json \
  --reference-filename plantstudio-main-window.gif \
  --filename-prefix golf-ui/club-preview/v002 \
  --output workflows/golf-club-object-v002.api.json
```

Generate a deterministic assembly graph:

```bash
python3 -m qwen_ui_pipeline assembly-workflow \
  examples/golf-club-assembly-v003.json \
  --reference artifacts/references/plantstudio-main-window.png \
  --generated artifacts/runs/golf-club-object-v002/image-02.png \
  --reference-filename plantstudio-main-window.png \
  --generated-filename golf-club-v002-2.png \
  --region 182,78,37,165 \
  --filename-prefix golf-ui/club-assembly/v003 \
  --output workflows/golf-club-assembly-v003.api.json
```

The approved brief must set `stage.status` to `approved` and record the selected
donor's `stage.approved_output_sha256`. Failed preflight, provider errors, and
ambiguous timeouts stop the stage; they never trigger a provider substitution or
automatic paid retry.

## First golf test

- v001 proved the complete provider-to-ComfyUI path, but its forced 4:3 output
  stretched the source.
- v002 used Alibaba's explicit `948*806` source-ratio output. Variant 2 was the
  strongest donor image.
- v003 composites only the 37×165 selected region at source resolution. Its
  measured absolute error outside that region is zero pixels.
- FigJam nodes `4:146`, `4:147`, and `6:146` contain the selected v002 render,
  its contact sheet, and the exact-preservation v003 assembly respectively.

See [the run evaluation](docs/runs/golf-club-object-v001-v003.md) and
[the prompting method](docs/research/qwen-image-3-prompt-method.md).
