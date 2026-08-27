# Style-research gate: board icons test (2026-08-27)

The non-paid gate preceding the four-icon animation test. No submission happens until this
gate's style lock, motion hypotheses, and exact estimates are recorded and the batch is
authorized (owner authorization: in-session instruction of 2026-08-27, "select and crop 4
icons and run this test").

## Source provenance

- FigJam board `SWuBeRWPrhVZ6GW2kqGz1o` ("Untitled", reference intake). Icons come from
  node `0:4` ("image 86"), a Ragnarok-style skill-tree window screenshot, exported via the
  repo Figma helper at max dimension 2048 (rendered 1617x1577).
- Four tiles cropped at 104x104 from that export; crop boxes and SHA-256 hashes in
  `../evidence/board-icons-test/source/` (`hashes.json`). The crops — not any redrawn
  version — are the identity authority.

## Style lock (what "that style" means, observed)

- 24px-origin pixel-art glyphs inside beveled rounded-square tiles; the export is already
  ~4.3x upscaled with soft pixel edges — that softened pixel look is part of the captured
  identity and must not be re-sharpened, smoothed, or vector-redrawn.
- Limited per-tile palettes (amber/cream, red/pink, silver/blue on dark); painterly
  dither inside glyphs; tile frame reads as UI chrome and must stay rigid.
- Icons sit in UI grids; there is no scene, lighting, or camera — any perspective,
  shadow, or modernization is drift.

## Anchor construction

Integer 4x nearest-neighbor upscale of each 104px crop (416x416) centered on a 640x640
uniform `#00FF00` matte — 640x640 matches the canvas Seedance Mini actually delivers for a
480x480 request (see `../evidence/to-spec-smoke/`). Green was chosen over the source
screenshot's magenta key because magenta is adjacent to the Heal tile's pink/red palette
and would raise both model-drift and keying-contamination risk; green is out-of-palette
for all four tiles. First frame = last frame = the anchor (loop attempt).

## Motion hypotheses (one restrained gesture each, glyph-only, frame static)

| Icon | Node-0:4 tile | Gesture |
| --- | --- | --- |
| `heal` | pink heart, red tile | one soft heartbeat pulse (~5% scale) |
| `protect` | silver shield, dark tile | one diagonal gleam sweep across the shield face |
| `blessing` | potion bottle, amber tile | one gentle tilt-and-return; existing sparkles twinkle once |
| `holy-light` | golden cross, cream tile | one soft brightness bloom of the existing rays |

These four span the addon's motion families (scale, specular sweep, rotation, luminance)
so the batch doubles as a per-family probe of how Seedance treats pixel-art identity.

## Routing, cost, and known model behavior

- `bytedance/seedance-2.0-mini` (study route), 4 s, `size 480x480` (delivered 640x640),
  seed 1, no audio. Estimate **$0.0756 per clip, $0.3024 for the batch** (billed
  $0.05432/clip in the prior smoke cell). Exact per-run estimates are acknowledged at
  submission per the run contract.
- Applied findings from the smoke cell: verify delivered dimensions rather than requested;
  do not spend cells on seed sweeps (2.x is prompt-dominated); expect endpoint drift —
  seam RMSE is a recorded diagnostic, not an acceptance claim.
- ComfyUI leg: the addon's planning nodes (`SeedanceIconPrompt` → `SeedancePlanRequest`)
  are executed for each brief and their compiled prompt / validated request / estimate
  recorded in `../evidence/board-icons-test/comfyui-plan.json` — the same request path the
  workflow template exposes in-graph, with paid submission still at the CLI gate.

## Acceptance framing

Studies, not finals: the reviewable questions are (per icon) did identity hold at pixel
level, did the gesture stay inside the tile, did the frame stay rigid, and how bad is the
loop seam. Human review happens on the PR/issue embeds.
