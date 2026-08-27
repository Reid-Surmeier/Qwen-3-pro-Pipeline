# Control variables

Every lever that changes a Seedance icon-animation result, grouped by where it lives.
Live OpenRouter metadata is always authority over the dated observations recorded here
(profiles observed 2026-08-27 via `seedance-icons capabilities`). Upstream parameter
semantics come from the BytePlus ModelArk survey in
`docs/research/seedance-comfyui-research.md` (observed 2026-08-26).

## 1. Request-level variables (OpenRouter `/api/v1/videos`)

| Variable | Where set | Observed range (2026-08-27) | Notes |
| --- | --- | --- | --- |
| `model` | `plan --model` | `bytedance/seedance-2.0-mini`, `bytedance/seedance-2.5` | `study` → Mini, `final` → 2.5; never silently switched (ADR 0002). Record alias **and** canonical slug (`…-20260811`, `…-20260807`). |
| `duration` | `plan --duration` | Mini 4–15 s; 2.5 4–30 s | Integer seconds. Unsupported values fail; a >15 s study does not become a final. |
| `size` | `plan --size` | Mini 13 sizes incl. `480x480`, `720x720`; 2.5 14 sizes incl. `640x640`, `960x960` | **Not an exact canvas in practice**: an accepted `480x480` request delivered 640x640 (Ark's native 480p 1:1 grid) — see `docs/evidence/to-spec-smoke/`. Treat `size` as resolution/ratio routing and verify delivered dimensions. Do not combine with `resolution` + `aspect_ratio`. |
| `resolution` + `aspect_ratio` | direct request only | `480p`/`720p`; ratios `1:1` … `21:9` (Mini also `9:21`) | Alternative to `size`; supply one addressing scheme, never both. |
| `seed` | `plan --seed` | Integer, both models | Weak lever on 2.x: the OpenRouter profile advertises `seed`, but upstream ByteDance treats even 1.x same-seed runs as "similar, not guaranteed identical", and ComfyUI's 2.x nodes warn results are non-deterministic regardless of seed. Log it for provenance; do not build determinism claims on it, and never assume a Mini seed transfers to 2.5. |
| `generate_audio` | `plan --audio` | Boolean, both models | Off by default for icons. Pricing SKU changes with audio (see §4). |
| `frame_images` | `plan --first-frame` / `--last-frame` | `first_frame`, `last_frame`, both models | Exact anchors. First-only = source-locked opening; first+last = endpoints or loop attempt. Matching anchors do **not** prove a seamless loop. |
| `input_references` | `plan --image-reference` / `--video-reference` / `--audio-reference` (repeatable) | image / video / audio URLs or data URLs | Style/motion/audio guidance, not exact frames. Documented precedence can mask references when mixed with anchors — mixing requires `--experimental-mixed-inputs` and is an experimental cell. |
| Passthrough params | direct request only | Mini: `watermark`, `req_key`, `return_last_frame`; 2.5: `watermark`, `req_key`, `output_format` | Per-model `allowed_passthrough_parameters` from the live profile. `return_last_frame` (Mini) matters for last-frame chaining studies; do not assume it exists on 2.5. |

## 2. Prompt-level variables (compiled from the motion brief)

`compile_prompt` renders the brief into labeled blocks, in order: SOURCE AUTHORITY, LOCKED
STYLE, MOTION, TIMING (optional), CAMERA, BACKGROUND / MATTE, MUST NOT. Each block is a
control surface:

- **source_authority** — identity contract: which asset is exact, what must be preserved.
- **style_lock** — silhouette, geometry, stroke, palette, negative space, typography, safe
  area, material treatment, downsample readability targets.
- **motion** — the one purposeful gesture: path, transform vs morph, secondary parts.
- **timing** — beats, first/last holds, ease-in/out, settle point, loop seam language.
- **camera** — lock language: orthographic front view, no pan/zoom/roll/perspective.
- **background** — matte policy: exact hex, no gradient/spill/shadow (ADR 0003: no native
  alpha claim; transparency is produced by keying and inspected separately).
- **negative_constraints** — forbidden drift: no redraw, no stroke/corner changes, no edge
  shimmer or color pulsing, no visible loop seam.

Wording inside these blocks is a variable like any other: change one block per study cell
(`docs/research/experiment-matrix.md` phases A–B are exactly this).

## 3. Conditioning modes (choose one per baseline run)

1. **Text only** — no identity lock; rarely acceptable for icon work.
2. **First frame** — source-locked opening, free ending.
3. **First + last frame** — endpoint control or loop attempt; loop closure still needs seam
   verification (`verify --loop`).
4. **References (image/video/audio)** — style or motion guidance in a separate baseline run,
   never mixed into the anchor baseline.

## 4. Cost variables

Estimate = `width × height × duration × 24 / 1024` video tokens × the live per-token SKU.
Observed SKUs (USD/token, 2026-08-27): Mini `0.0000035` (with or without audio),
`0.0000021` with video input; 2.5 `0.0000107`, `0.0000064` with video input. Reference
points: Mini `480x480` × 4 s ≈ $0.0756; Mini `720x720` × 6 s ≈ $0.2552. The estimate is
not an invoice; the exact decimal goes to `submit --acknowledge-cost`.

## 5. Upstream constants (not controllable on any surface)

From the ModelArk survey: there is **no negative prompt, no CFG/guidance scale, and no
sampler/step control** on any Seedance surface (Ark, fal, Replicate, OpenRouter, ComfyUI)
— negative intent lives only in the MUST NOT prompt block. **FPS is fixed at 24**; frame
rate changes only through post-processing. There is **no native loop flag**; loops are
approximated with identical first/last anchors plus seam verification. `camera_fixed`
exists only on Seedance 1.x (not routed here) — on 2.x models the camera lock is purely
prompt language, which is why the `camera` brief block matters.

## 6. Variables outside the request

- **Source export** — canvas, safe-area margin, export scale, and the SHA-256 that locks it.
- **Model iteration transfer** — re-run winning studies on 2.5 before acceptance; behavior
  is not assumed equivalent between models or canonical versions.
- **Post-processing** — keying the matte, downscale review at 16/32/48/64 px, optional frame
  interpolation or upscaling (see `comfyui-pipeline.md`). These change the deliverable, not
  the generation, and must be recorded as separate evidence.
