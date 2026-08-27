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

| Metric | Role | Catches |
| --- | --- | --- |
| `min_silhouette_iou` ≥ 0.90 | certification decision | redraws and motion escaping the tile — zero-overlap separation across both calibration batches (faithful 0.998–1.0 vs violations 0.57–0.76) |
| `unique_frames` 2–8 / `effective_fps` ≤ 10 | certification (by construction) | non-sprite cadence |
| `out_of_palette_pixels` = 0 | certification (by construction) | palette drift |
| `frame0_identity` | recorded diagnostic only | demoted after batch 2: it tracks tile paleness, not fidelity (faithful 0.71–0.84 overlapping the true redraw's 0.72); anchor RMSE from `verify` covers frame-0 fidelity |

`certified: false` → the run is a rejected candidate (kept as evidence); iterate the
brief or seed. Only certified conformed output goes to human style review, presented
beside its anchor.

## Calibration provenance

Calibrated on the two 2026-08-27 board-icons batches (9 runs, Issue #87). Batch 1: the
gate certifies exactly the two humanly-acceptable runs (heal 1.00, protect 0.998) and
rejects both failures (blessing redraw 0.76, holy-light escape 0.61). Batch 2 (era-corpus
briefs): all five certified at IoU 0.998–1.0 — and exposed frame0_identity as
paleness-biased, leading to its demotion to a diagnostic. Recalibrate against human
verdicts as batches accumulate; thresholds live in `RetroThresholds`
(`src/seedance_icons/retro.py`).
