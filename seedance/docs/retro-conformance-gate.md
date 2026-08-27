# Retro-conformance gate

For pixel-art sources, raw Seedance output is never the deliverable and never the thing a
human is asked to approve. Research basis: `research/retro-sprite-animation-authenticity.md`
— Seedance is architecturally a smooth 24 fps interpolator with no cadence, palette, or
no-repaint control, while authentic low-bit animation is 2–8 held frames on a fixed
indexed palette with pixel-snapped motion. (Ragnarok Online's own item/skill icons are
static in-client; animating them is a deliberate stylistic extrapolation.)

## The two gate layers

**1. Pre-generation (brief lint).** Briefs for pixel-art sources must use sprite grammar:

- no style tokens (`pixel art`, `8-bit`, `retro`, `sprite`, `glow`, `bloom`, `particles`,
  `cinematic`) — style comes from the anchors; those tokens trigger re-rendering;
- one concrete small motion clause, stop-motion vocabulary ("held poses", "visible
  steps"), static camera, plain still background;
- hard containment negatives ("nothing may cross the edge of the square");
- exact anchors on both ends.

Reference briefs: `../docs/evidence/board-icons-test/briefs-v2/`.

**2. Post-generation (deterministic conformance + certification).**
`seedance-icons retro-conform <run> --reference <anchor>` runs the pipeline from the
research note (temporal subsample → dedupe to ≤8 frames → NEAREST grid-snap → palette
lock to the anchor with no dither → NEAREST re-upscale → held-cadence reassembly) and
writes `<run>/retro/` with frames, `conformed.gif`, and `retro-report.json`. Temporal,
palette, and grid conformance are guaranteed by construction; the report's real decisions:

| Metric | Threshold | Catches |
| --- | --- | --- |
| `min_silhouette_iou` | ≥ 0.90 | redraws and motion escaping the tile (primary detector) |
| `frame0_identity` | ≥ 0.80 | model repainting the icon (calibrated 2026-08-27: faithful 0.82–0.84 after codec loss, redraws 0.72–0.77) |
| `unique_frames` / `effective_fps` | 2–8 / ≤ 10 | non-sprite cadence (by construction) |
| `out_of_palette_pixels` | 0 | palette drift (by construction) |

`certified: false` → the run is a rejected candidate (kept as evidence); iterate the
brief or seed. Only certified conformed output goes to human style review, presented
beside its anchor.

## Calibration provenance

Thresholds were calibrated on the four-run board-icons batch (Issue #87): the gate
certifies exactly the two runs a human judged acceptable (heal, protect) and rejects the
two failures (blessing: redraw+tilt, IoU 0.76; holy-light: bloom escape, IoU 0.61).
Recalibrate against human verdicts as batches accumulate; thresholds live in
`RetroThresholds` (`src/seedance_icons/retro.py`).
