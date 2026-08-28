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

## Batch 2 — era-corpus briefs (2026-08-27, five new icons)

Briefs written strictly from `../../research/era-ui-animation-reference-corpus.md`
prescriptions (each brief records its `era_idiom_basis`). Same config as batch 1.
Billed $0.05432 each — $0.27160 for the batch against a $0.378 estimate.

| Icon | Era idiom | First RMSE | Seam RMSE | Silhouette IoU | Certified |
| --- | --- | --- | --- | --- | --- |
| resurrection | FF6 save-point shimmer (2-state core blink) | 4.6 | 29.4 | 0.998 | yes |
| aqua-benedicta | cursor-sparkle glint walking the water line | 4.8 | 22.7 | 1.000 | yes |
| sanctuary | ALttP gold-tone blink, zero movement | 5.0 | 27.8 | 0.999 | yes |
| angelus | 1 px wing-tip flap (1-2-3-2) | 4.8 | 24.3 | 1.000 | yes |
| gloria | binary ray-tip twinkle | 4.9 | 25.5 | 0.998 | yes |

### Batch-2 findings

1. **Era-grounded briefs eliminated the structural failures.** No redraws, no
   containment escapes anywhere (batch 1: 2/4 failed). Silhouette IoU 0.998–1.0
   across all five.
2. **frame0_identity demoted to a diagnostic.** Across nine runs it tracks tile
   paleness, not fidelity (faithful 0.71–0.84 overlapping the true redraw's 0.72),
   while IoU separates with zero overlap. Certification now rests on IoU plus the
   by-construction checks; anchor RMSE from `verify` covers frame-0 fidelity
   (4.6–5.0 across this batch).
3. Endpoint drift persists (seam RMSE 23–29) — unchanged from batch 1 and unfixed
   by prompt work; loop closure remains a post-step (trim/cross-fade) or a
   first-frame-only conditioning question for a future cell.

## Batch 3 — beat-by-beat, reference-paired, complex-motion cells (2026-08-27)

Redesign per owner feedback: every run paired with a real-game reference animation
(`../references/`, provenance with sha256s), prompts at 406–543 compiled words
(`briefs-v3/`), crisp 26 px-grid anchors as both frame inputs, and four cells beyond
the subtle-idle layer. Seven runs billed $0.05432 each — $0.38024 against a $0.4990
estimate. One extra free finding: `input_references` reject data URLs
(`400 Only HTTPS URLs are allowed`) — the video-reference cell fetches its clip from
the repo raw URL.

| Cell | Idiom | First RMSE | Last RMSE | Silhouette IoU | Certified |
| --- | --- | --- | --- | --- | --- |
| heal | Emerald party-icon 2-pose loop | 4.2 | 39.6 | 0.942 | yes |
| angelus | quantized 1-2-3-2 wing flap | 4.1 | 43.8 | 0.965 | yes |
| protect | WoW cooldown clock-wipe + end flash | 4.0 | 14.6 | 0.422 | **no** |
| resurrection | press-fire + queued red blink | 4.1 | 24.2 | 0.863 | **no** |
| gloria | TCG 8-pose coin spin | 4.1 | 25.0 | 1.000 | yes |
| blessing | item-get pop + sparkle cycle | 4.3 | 22.5 | 0.395 | **no** |
| gloria-vidref | coin spin + real clip as video reference | 4.1 | 22.8 | 1.000 | yes |

### Findings (visually confirmed frame-by-frame; gate agreed with the eye on all seven)

1. **The transition layer works: both gloria spins certified at IoU 1.0.** The stepped
   coin-flip idiom transfers cleanly — full face → narrowed → thin edge → back → face,
   tile rigid, matte clean. First complex-motion successes of the experiment. The
   video-reference cell rendered rounder, more coin-like turn poses than the
   prompt-only cell — reference conditioning visibly steers pose drawing.
2. **Overlay grammar fails as a class.** All three failures treat overlay effects as
   scene events: protect applied the "dark cover" to the entire canvas (matte included)
   and its end flash bloomed across the matte; resurrection rendered the press as a
   whole-tile morph and never showed the red blink; blessing deleted the tile frame
   while the bottle bounced (figure/ground confusion — the licensed sparkles themselves
   were rendered correctly). Prompt language cannot yet buy WoW-style layers-above-the-
   icon; candidate next cell: composite overlays deterministically in post and reserve
   the model for glyph motion.
3. **Crisp anchors set a new first-frame record** (RMSE 4.0–4.3 vs 4.6–5.1 soft) and
   survived quantization — but sub-glyph detail below the 26 px grid (heal's tiny 'AB'
   mark) drops out after frame 0.
4. **Long continuous loops risk terminal drift**: angelus held near-static for seven
   conformed frames then broke identity on the last (last RMSE 43.8) — the endpoint
   anchor bounds the start tightly, not the end, exactly as in batches 1–2.

Per-run evidence in `<icon>-v3/` (gloria-vidref-v3 for the reference-conditioned cell).
