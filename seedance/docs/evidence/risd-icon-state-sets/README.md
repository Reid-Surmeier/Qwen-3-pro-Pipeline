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

## Take four: the sweep

`v4-sweep-animated.gif`, `v4-sweep-poses.png`, `v4-sweep-brief.json`.

Reid, on take three: *"it works, but again it's very static, there should be more
movement besides a hover animation — review the later stages of the seedance ticket and
see how that helped."*

Measuring the briefs answers it. Motion-field length against outcome, every brief on disk:

| Motion field | Runs | Outcome |
| --- | --- | --- |
| 24-32 words, 0 named poses | batch 1, batch 2 | a two-frame twinkle; batch 2 certified 0.998-1.0 |
| 64-76 words, 0 named poses | takes 1 and 3 | large gesture summarised; element moved ~15x further than asked |
| 123-218 words, 3-6 poses | batch 3, magazine-flip | large gesture written pose by pose; all certified |

The later stages did not get smaller and tighter. They got **bigger and enumerated** — a
full coin spin as eight named held poses, grounded in the game's own frame table. Every
attempt here to fix wandering by clamping the movement harder made the icon more static
without making it more faithful.

Take four asks for an eleven-pose examining sweep: 248 motion words, 9 named poses, the
glass travelling a fifth of the tile per pose across the whole head with the lens
contents changing as it goes. 40.1% of pixels differ at the peak of the cycle. The bust
holds still throughout and the cycle returns to its starting pose.

Remaining defect: the glass grows and shrinks slightly through the sweep, which the
brief forbids. Worth one more pass; it is not the icon falling apart.

## The reference animation, and why you could not see it

Reid: *"what reference animation are you giving it? I don't see that in the PR. Did you
load a reference video?"*

Yes — and the PR never showed it, which is a fair complaint about the PR rather than the
run. `REFERENCE-coin-spin.gif` is the animation every sweep run was given, passed as a
video URL in `input_references`, verifiable in each run's `request.json`. It is the
Pokemon TCG duel coin's full eight-step spin, reconstructed from the game's own
`AnimData167` frame table, 224x224, seven frames, 0.47 seconds.

It is the **cadence** authority, not the shape authority: one large gesture, many flat
held poses, a steady beat, returning to the pose it began in. Nothing about a coin is
meant to appear in a magnifying glass.

## Take five: the Anchor had nowhere to move

Reid on take four: *"the motion is jerky and the icon moves outside the green window box."*

Both were real, and the second was a mistake in the Anchor rather than the brief.

**Outside the box.** Take four's Anchor was built by cropping the icon to its own content
and scaling it to fill the square — which threw away the margin the icon was drawn with.
Measured afterwards, its drawing bbox and its tile bbox were identical on all four sides:
zero margin. A gesture needs somewhere to happen, and with no room inside the tile the
only free space was outside it. `inner_margin` now refuses such an Anchor, and the
rebuilt one keeps the icon's own margins (7.8% of tile width) inside a 384px tile with a
48px border.

**Jerky.** The full-cycle GIF was four states' frames concatenated, each deduped inside
its own quarter, so the groups carried different pose counts and different amounts of
change. `full-cycle.gif` now dedupes the take as a whole and holds every pose for the
same time, which is what the era's frame tables do.

`border_leak` also went in: in filled framing the key colour is the tile edge, so it is
also the containment test — a question the framing can actually answer, unlike every
fidelity metric tried for filled tiles.

### Take five result, and the trade-off it exposes

Containment holds: `inner_margin` 7.8%, `max_border_leak` **0.0** across all thirty-two
frames, the green border the same thickness on all four sides in every pose. The cycle is
eleven poses at an even 100 ms.

But the movement is smaller: **23.0% of pixels differ at the peak, against 40.1% in take
four.** That is the trade-off, and it is structural rather than a brief failure. The tile
is the arena. Take four moved further precisely because it was escaping; keeping the
glass inside a tile whose margin is 7.8% of its width caps how far it can travel.

Getting both means drawing the icon smaller inside its tile — more margin, so more room
to sweep — which costs detail at 64 pixels. That is an icon-design decision, not a
pipeline one.

| Take | Framing | Movement at peak | Stayed in the tile |
| --- | --- | --- | --- |
| 3 | filled, no margin | ~static | yes (nothing moved) |
| 4 | filled, no margin | 40.1% | **no** |
| 5 | tile with 7.8% margin | 23.0% | **yes** |

## Take six: the right kind of reference, and pacing by travel

Reid on take five: *"the movement is still quite jerky, and the reference video you gave
has nothing to do with the animation shown ... the coin animation's movement is affecting
the way the magnifying glass moves in a strange way. That should be hard wired."*

Both true, and the first explains a failure previously blamed on the brief.

**The reference kind.** `ref-coin-spin` is a **rotation** — a coin turning about its axis
in place. It was handed to a brief asking a magnifying glass to **travel**. The glass
tumbled and changed size instead of travelling, and no brief wording corrected it,
because the reference was pulling the other way throughout. The five references are now
classified by `motion_kind` in `provenance.json`, and `check_reference_matches_motion`
refuses a run whose kinds disagree.

Only `ref-textbox-arrow-bob` is a translation. Take six uses it. **The model's own
pacing improved before any post-processing: raw step spread 2.138 with the coin, 1.018
with the arrow.** The reference teaches the kind of movement, not only its beat.

**The pacing.** Per-step travel of the moving element in take five ran

    0 0 0 0 0 1 26 66 10 13 9 11 6 14 24 98 13 73 32 17 26 40 9 41 0 0 0 ...

Long stretches of nothing, then leaps of a hundred pixels; spread 2.1x its own mean.
Equal hold times cannot fix that, because the unevenness is in the content.
`resample_by_travel` picks frames spaced evenly along the path the element travels,
which is what a hand-authored frame table does.

| Take | Reference | Raw step spread | After resampling | Border leak |
| --- | --- | --- | --- | --- |
| 5 | coin spin (rotate) | 2.138 | 0.424 | 0.0 |
| 6 | arrow bob (translate) | **1.018** | **0.199** | 0.0095 |

**Still wrong, and the next thing to fix:** the bust does not hold still. It is specified
as frozen and it visibly changes across poses. Filled framing has no fidelity metric, so
nothing catches this but a person looking. A targeted one is possible — mask out the
cobalt glass and compare only the marble across frames — and would catch exactly this.

**Still missing:** a large-travel translation reference. The arrow bob moves 2 px. Both
pret and The Spriters Resource were searched for a magnifier or sweep with a documented
frame table and neither has one. Amplitude currently comes entirely from the brief.
