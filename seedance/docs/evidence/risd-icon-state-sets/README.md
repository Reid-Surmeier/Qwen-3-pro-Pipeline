# RISD icon State Sets — evidence

Two four-state Motion Passes of the same icon (UI-01 Search, RISD museum browser),
2026-08-30. Together they calibrated `min_anchor_silhouette_iou` and exposed the
Anchor-shape hole that `mask_fill_ratio` now closes.

| File | What it shows |
| --- | --- |
| `stills-1k-candidates.png` | One Asset Pass, four Qwen candidates at 1024px. Too fine to be sprites — deliberately. |
| `stills-reduced-to-64px.png` | The same four after `snap_and_lock` at grid 64 against the anchor palette: 13 colours each, genuine 64px icons. Reid's original bust is first, for scale. |
| `take1-certified-but-broken.png` | Take one, all four states **certified**, two visibly wrong: the magnifier floats free with an empty lens in `hover` and flattens into an ellipse in `pressed`. The Anchor carried an opaque white panel, so the silhouette mask was a rectangle and every IoU read 1.0. |
| `take2-anchor-and-four-states.png` | Take two with a keyed Anchor and a rigid-stamp brief. Left to right: Anchor, idle, hover, pressed, settled. Deformation is gone; displacement is not — the brief asked for two sprite pixels and got roughly fifteen. |
| `take2-states-report.json` | The certification record for take two. |

## The numbers that separated

| State | within-state IoU | IoU vs Anchor | Human verdict |
| --- | --- | --- | --- |
| idle | 0.734 | **0.979** | accept |
| hover | 0.994 | **0.466** | reject |
| pressed | 0.991 | **0.529** | reject |
| settled | 0.973 | **0.955** | accept |

Within-state stability says nothing about whether the state is still the icon: the two
rejected states were the *most* stable of the four. The Anchor comparison separates
cleanly, with nothing between 0.529 and 0.955, so it became a certification check.

## What is still unresolved

Seedance will not honour a one-or-two sprite-pixel displacement. Told to move an
element two pixels it moves it fifteen, in both takes and under two very different
briefs. `idle` and `settled` — the two states that ask for *no* movement — are correct
in both takes. The moving states are not.
