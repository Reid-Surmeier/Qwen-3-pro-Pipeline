# Board-icons test — batch results (2026-08-27)

Four Seedance 2.0 Mini studies (4 s, seed 1, no audio, requested 480x480 → delivered
640x640) from the gate in `../../research/board-icon-style-gate.md`, Issue #87. Billed
$0.05432 each — $0.21728 for the batch against a $0.3024 estimate.

| Icon | Gesture | First RMSE | Last RMSE | Seam RMSE | Study verdict (pending owner review) |
| --- | --- | --- | --- | --- | --- |
| heal | heartbeat pulse | 4.7 | 26.8 | 23.8 | Identity held at pixel level; pulse contained in tile; endpoint returns close but not exact. Best of batch. |
| protect | diagonal gleam | 4.6 | 34.6 | 31.8 | Identity held; gleam reads correctly; slight glow spill below the tile's bottom edge. |
| holy-light | ray bloom | 5.1 | 30.4 | 26.9 | Cross and tile recognizable, but the bloom bursts far outside the tile across the matte — violates containment and threatens keying. |
| blessing | bottle tilt | 4.9 | 73.9 | 71.1 | FAILURE: starts on-anchor then the model redraws the icon in modern crisp pixel-art and tilts the whole tile into a plate. Both no-redraw and rigid-frame locks broken. |

## Findings

1. **Luminance and scale gestures respect pixel identity; rotation invites redraw.** The
   "tilt" wording licensed whole-tile reinterpretation. Next-cell hypothesis: rephrase as
   a sub-element gesture ("the bottle sways within its frame, the tile and outline remain
   exactly as drawn") or drop rotation for pixel-art sources.
2. **Containment needs its own negative constraint.** "Motion contained inside the tile"
   did not stop glow spill (protect, mild; holy-light, severe). Add an explicit "no light,
   glow, or rays may cross the tile boundary onto the matte" clause.
3. **First-frame adherence is excellent** (RMSE 4.6–5.1, better than the smoke cell's
   6.3) — the 640x640 anchor matching the delivered canvas likely helped.
4. Endpoint drift remains the weak axis everywhere, as in the smoke cell: first = last
   anchors bound the start tightly, not the end.

Per-run evidence in `heal/`, `protect/`, `blessing/`, `holy-light/`: output.mp4 + sha256,
sanitized request, plan, terminal job record, verification report, GIF preview, mid frame.
