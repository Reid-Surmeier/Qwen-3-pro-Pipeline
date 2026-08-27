# Issue 51 — first closed-loop run, PlantStudio main window

One UI screenshot taken from source to an independently judged verdict, through
every stage of the loop.

Source: `artifacts/references/plantstudio-main-window.png`, 474x403, a genuine
late-1990s application window.

## 1. Component extraction — deterministic, free

Seven named UI elements were declared in `components.json` and extracted with
`component-workflow` on the local ComfyUI pool. No model was involved.

| Component | Rectangle | Extracted | Pixel-exact |
| --- | --- | --- | --- |
| `title-bar` | 4,4,466,18 | 466x18 | yes |
| `menu-bar` | 4,22,466,21 | 466x21 | yes |
| `toolbar` | 4,44,466,26 | 466x26 | yes |
| `plant-canvas` | 4,72,466,176 | 466x176 | yes |
| `species-list` | 4,253,155,120 | 155x120 | yes |
| `growth-graph` | 164,253,306,120 | 306x120 | yes |
| `tab-strip` | 164,375,306,20 | 306x20 | yes |

Every crop was compared byte for byte with the corresponding rectangle of the
source. All seven matched exactly. See `component-contact-sheet.png`.

This is the reverse-engineering step: the screenshot is now a set of
independent, individually addressable elements rather than one flat image.

## 2. Render Pass — one bounded paid edit

`brief.json` licensed exactly one change: the title-bar caption's plant count
from 11 to 24. Compiled prompt: 1,010 of the 4,500 token budget.

Two provider rejections occurred before any billing, both schema-level:
`aspect_ratio: "source"` and then `"auto"` are not accepted for this model. A
subsequent request with `5:4` and `count: 2` timed out at the client's 180
second read limit. Following the rule that provider ambiguity after submission
must fail closed, it was **not** retried blindly; the account's usage counter
was read instead and showed no change, establishing that the timed-out request
did not bill. The batch was reduced to one image and rerun.

**Qwen made the requested text edit and then redrew the entire window** —
different plants, shifted layout, altered tab strip. This is the drift the
region-assembly design exists to contain.

## 3. Assembly

`ReferenceRegionComposite` took only rectangle `4,4,466,18` from the generated
image and restored the authoritative source everywhere else.

## 4. Gate 1 — deterministic

```text
invariant pixels: pass
  region title-bar-caption: 8350/8388 pixel(s) changed
```

Zero invariant violations. Despite the model redrawing the whole window, every
pixel outside the licensed rectangle is byte identical to the source.

## 5. Gate 2 — independent review

Reviewer: `anthropic/claude-opus-4.5`. Builder: `qwen/qwen-image-3-pro`. The
client refuses to run a reviewer from the builder's family.

The gate ran three times, and each run changed the harness rather than the
image. This is the loop working as designed.

| Run | Configuration | Verdict | Correct? |
| --- | --- | --- | --- |
| 1 | crops only, native size | `defect` — "candidate shows '24 plants' while baseline shows '11 plants'" | **False positive.** The reviewer was never told what change was licensed, so it reported the intended edit as a fault. |
| 2 | licensed intent supplied | `match`, confidence 0.92 | **False negative.** It accepted a caption that is visibly misregistered and blurred. |
| 3 | intent + 4x nearest-neighbour magnification | `defect` (`visual-state`) at (100, 12), confidence 0.95 — "rendered with heavy antialiasing/smoothing rather than the crisp aliased bitmap font of the source" | **Correct.** Matches an unaided human read of `titlebar-comparison.png`. |

Two harness defects were found and fixed by running the loop:

1. **The reviewer needs the licensed intent.** Without it every deliberate
   change reads as a defect. `RegionReview.intent` now carries it.
2. **Bitmap defects are invisible at native size.** An 18 pixel tall band gives
   a reviewer too little to judge. Nearest-neighbour magnification adds no
   information but lifts the defect above the reviewer's threshold; both crops
   are magnified equally. `scale` now defaults to 4.

Both fixes are covered by tests.

## 6. Result

Final status: `revision-required`, routed to `render-pass`.

The finding is correct and its root cause is identifiable: the Render Pass was
produced at 1024x820 and resampled down to 474x403, which destroys the source's
crisp aliased bitmap character. The next iteration should render at native size
or confine the pass to the region itself rather than the whole window.

The loop did not declare success on a flawed result, and no human had to point
the defect out.

## Cost

| Item | Cost |
| --- | --- |
| Render Pass, 1 image (`qwen/qwen-image-3-pro`) | $0.043000 |
| Review run 1 | $0.00601 |
| Review run 2 | $0.00671 |
| Review run 3 | $0.00827 |
| **Total** | **$0.06399** |

Measured as the delta in the OpenRouter account usage counter, plus the exact
per-call `usage.cost` the reviewer returned. One image generated, well inside
the ten-image ceiling of ADR 0003.
