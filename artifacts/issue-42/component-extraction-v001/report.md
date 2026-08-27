# Issue 42 — lossless component extraction, live verification

Deterministic proof that `component-workflow` produces independent, pixel-exact
component crops with no model call.

## Method

1. Uploaded `source-reference.png` (512x512) to the local ComfyUI pool. It is the
   region-composite verification image: a red reference field with a blue
   generated rectangle at `100,100,200,200`.
2. Declared two components in `components.json`:
   `reference = [0,0,100,100]` (inside the untouched red field) and
   `generated = [100,100,200,200]` (exactly the blue rectangle).
3. Built `extraction.api.json` with
   `qwen-ui-pipeline component-workflow` and enqueued it unmodified.

## Result

| Component | Expected size | Actual size | Expected centre | Actual centre |
| --- | --- | --- | --- | --- |
| `reference` | 100x100 | 100x100 | red `(255,0,0)` | `(255,0,0)` |
| `generated` | 200x200 | 200x200 | blue `(0,0,255)` | `(0,0,255)` |

Both crops match their declared rectangles exactly. No provider request was made
and no pixels were regenerated; the graph is `LoadImage -> ImageCrop -> SaveImage`
per component.

## Provenance

- ComfyUI pool: `main@27bee23` custom nodes, router `10.255.255.254:8188`.
- Prompt executed with `status: success`.
- Paid providers: not used. Cost: $0.
