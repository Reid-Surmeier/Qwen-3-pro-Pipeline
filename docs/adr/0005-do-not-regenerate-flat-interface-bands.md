# 5. Do not regenerate flat interface bands, and detect it for free when it happens

Date: 2026-08-26

Status: accepted on 2026-08-26.

## Context

The first closed-loop run (Issue 51) licensed a single change: the numerals in
a title-bar caption. The Render Pass made that change correctly and the region
assembly contained the model's incidental redraw of the rest of the window
completely — zero unlicensed pixels changed.

The result was still wrong. The regenerated caption lost the source's crisp
aliased bitmap character. Detecting that took a paid vision review, and the
review only found it after two harness fixes: supplying the licensed intent,
and magnifying the crops.

Measuring the run afterwards showed the defect is both cheaper to detect and
harder to repair than it first appeared.

The source title-bar band contains **seven unique colours**. It is a flat,
palettised control from an era of indexed-colour interfaces. Every way of
resampling the generated 1024x820 render down to the source's 474x403 yields a
band of roughly 2,600 to 2,900 colours:

| Downsample | Unique colours | Hard edges |
| --- | --- | --- |
| source | 7 | 1036 |
| LANCZOS | 2804 | 1045 |
| NEAREST | 2611 | 953 |
| BILINEAR | 2900 | 863 |
| BOX | 2782 | 1005 |

The choice of filter is not the cause, so no filter change is the cure. A
continuous-tone generative process does not produce a seven-colour band, and
resampling cannot restore one that was never generated.

## Decision

Generative Render Passes are not the right tool for editing flat palettised
interface bands — captions, labels, menu text, and similar indexed-colour
chrome. Such edits belong in deterministic composition, which is the same
principle ADR 0002 applies to pixels outside an edit region, extended to the
rendering character of the pixels inside one.

When a Render Pass does redraw such a band, the loop detects it in the free
deterministic layer rather than paying for the judgement. `compare_palettes`
reports each licensed region's palette growth against the baseline, and growth
beyond the contract's tolerance means the region lost its rendering character.

Palette growth is reported alongside `FidelityResult` rather than folded into
its `passed` flag. `passed` answers one precise question — did unlicensed
pixels change — and overloading it would make both answers harder to act on.

## Consequences

A defect class moves from the paid semantic layer to the free deterministic
one. On the Issue 51 candidate the check reports `7 -> 2804 colour(s), 400.6x`
with no model call, catching in milliseconds what previously cost a review and
two harness fixes to see.

This is the promotion rule from the convergence loop applied to itself: a
finding became a reproducible test rather than being re-reported.

The tolerance is a judgement, not a law. A region licensed to gain a gradient
or a new coloured control legitimately grows its palette, so `max_growth`
belongs to the contract and defaults deliberately loose at 4.0. The signal this
check exists for is hundreds of times larger than that.

Bitmap text edits now need a deterministic path. That path does not exist yet,
and it is not free either: composing a caption from the source's own glyphs
requires every glyph to appear somewhere in the source, which for arbitrary
text it will not. Some edits will need a different source of type, and that is
a real limitation to design against rather than assume away.
