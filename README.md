# Qwen UI pipeline

A reference-preserving UI workflow built around Qwen Image 3 Pro, ComfyUI,
Figma/FigJam, and deterministic application code.

## Current machine setup

- ComfyUI `0.31.0` runs as the enabled user service `qwen-comfyui.service`.
- The service can run a five-worker pool behind the same ComfyUI API address,
  allowing separate agents' Render Passes to execute without one local FIFO.
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

The worker router changes only queue assignment. Edit Brief compilation,
workflow JSON, provider selection and fallback, fixed seeds, image outputs,
Assembly, and provenance remain inside the existing pipeline. See
[`deploy/README.md`](deploy/README.md) for pool configuration and installation.

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
  --reference-filename plantstudio-main-window.png \
  --generated-filename golf-club-v002-2.png \
  --region 182,78,37,165 \
  --filename-prefix golf-ui/club-assembly/v003 \
  --output workflows/golf-club-assembly-v003.api.json
```

For stickers and other non-rectangular assets, build an additive mask-owned
Assembly graph. This keeps the original rectangle path intact while assigning
approved artwork, white cutline, and generated material contact to separate
masks:

```bash
python3 -m qwen_ui_pipeline mask-assembly-workflow \
  --reference-filename device.png \
  --artwork-filename approved-sticker.png \
  --mask-filename approved-sticker-mask.png \
  --integration-filename qwen-contact-donor.png \
  --canvas-width 1024 \
  --canvas-height 768 \
  --target-quad 120,90,430,72,448,350,105,366 \
  --cutline-width 3 \
  --contact-width 2 \
  --filename-prefix stickers/mask-owned/v001 \
  --output workflows/sticker-mask-assembly-v001.api.json
```

The contact donor must already be a full-canvas image. Only its narrow contact
band is used. The approved artwork is warped together with its mask, then
composited deterministically; the graph fails before saving if source pixels
outside the editable union or artwork-owned pixels drift. See
[`docs/adr/0004-mask-owned-sticker-assembly.md`](docs/adr/0004-mask-owned-sticker-assembly.md).

`provider: auto` tries OpenRouter first. It falls back to direct Alibaba only
for OpenRouter's pre-generation privacy/guardrail rejection, not after a
timeout or ambiguous error that could create duplicate billing.

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
