# Local Qwen Image 3 Partner-compatible nodes

The local nodes mirror the concepts in ComfyUI's Qwen Image 3 Partner Nodes
while continuing to use this repository's explicit OpenRouter and Alibaba
adapters. They do not use the Comfy Partner proxy or store credentials in a
workflow.

## Node surface

`Qwen Image 3 Text to Image (Local)` exposes provider, model, prompt, negative
prompt, width, height, output count, seed, prompt expansion, and watermark.

`Qwen Image 3 Edit (Local)` adds `image_1`, `image_2`, and `image_3` plus the
`auto`, `match input`, and `custom` size concepts. Each named socket accepts
one image, not a batch, so `@Image2` always means the visibly connected
`image_2`. The node rewrites those tags to the provider's ordered `Image N`
form before request construction.

Both nodes return:

1. an IMAGE batch;
2. the normalized Edit Brief JSON;
3. run metadata with provider/model identity, requested and completed counts,
   controls, reference roles and hashes, output hashes, usage, and request ID
   when returned.

## Provider boundary

| Control | OpenRouter | Alibaba |
| --- | --- | --- |
| Three ordered references | yes | yes |
| Count 1-6 and seed | yes | yes |
| Negative prompt | rejected when non-empty | native parameter |
| Prompt expansion | rejected when enabled | native parameter |
| Watermark | rejected when enabled | native parameter |
| Automatic edit size | rejected | omit `size` |
| Match/custom size | advertised Qwen dimensions only | exact documented dimensions |

Validation completes before a provider client is constructed. The saved
portable example therefore uses a 1024 by 1024 custom size with the three
provider-specific toggles off; switching only the provider widget requires no
reference, Assembly, preview, or save rewiring.

OpenRouter capability records can change. Re-check the live endpoint record
before paid use. Alibaba's current direct API documents a maximum area of
2048 by 2048 even though the pinned Comfy Partner source accepts a larger
area; the direct adapter keeps the smaller provider limit.

## Existing workflow compatibility

`QwenImage3Render` remains registered with the same `edit_brief_json` and
`reference_images` inputs. Existing API workflows need no migration. New
human-reviewed graphs should use the visible nodes and keep the emitted Edit
Brief/run metadata for automation and provenance.

The evidence files are:

- `workflows/partner-three-reference.api.json` for API validation;
- `workflows/partner-three-reference.workflow.json` for visual loading in the
  ComfyUI canvas.

The canvas file groups each Load Image and Preview Image lane under its exact
`image_1`, `image_2`, or `image_3` role, then previews and saves the IMAGE batch.
Replace the placeholder image filenames after loading it.

## No-cost verification

Run mocked compatibility checks without credentials or generation:

```bash
python3.12 -m unittest \
  tests.test_partner_controls \
  tests.test_comfyui_node \
  tests.test_comfyui_workflow \
  tests.test_remote_review -v
```

On the host, run the read-only listener/schema audit against the routed
endpoint after deployment:

```bash
python3.12 scripts/audit_comfyui_review_path.py \
  --router-url "${QWEN_COMFYUI_REVIEW_URL}"
```

This check reads sockets, loopback addresses, system stats, queue state, and
the two node schemas. It neither submits a prompt nor changes network state.

The installed custom-node wrapper imports this Python package. After the
change reaches the host's canonical checkout, first verify the routed queue is
empty, then restart the existing ComfyUI service and run the audit above. Do
not change the five-worker router, listener addresses, or Tailscale routes as
part of this deployment.
