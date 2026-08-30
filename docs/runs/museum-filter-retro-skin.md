# Re-skinning a museum filter panel as an RO-style options window

Issue [#118](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/118).
Reference Screen: `artifacts/references/museum-filter-retro-skin-v001/style-ro-options-window.png`
(SHA-256 `7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16`).

## Outcome

**Four full-redraw Render Passes failed to reach the required fidelity, so the
work moved to Assembly.  After owner review, one final two-output Qwen edit pass
supplied bounded header, lettering and tab donors for Assembly v002.**

## What each pass got wrong

| Pass | Change | Owner's verdict |
| --- | --- | --- |
| v001 | Two references, style + data card, 2:3 portrait | Layout came from the data card, not the style window. Modern sans. Slider thumb sat on the left arrowhead. |
| v002 | Dropped the data reference; layout copied the BGM/Effect row order, 16:9 | Over-corrected — slavishly copied the reference's row order. Text off, everything cramped, colour drift. |
| v003 | Any/All became two checkboxes, 4:5, palette pinned to sampled hexes | Size right. Font still too thick. Tabs wrong. Checkboxes not exact. Title misaligned. ✕ button wrong. |
| v004 | Second reference: a 2–4× magnified parts sheet cut from the original | Closer on every axis, still not the original's chrome. |
| v005 | Assembly v001 became the composition authority; the original and parts sheet became style authorities; 3:2 final edit | Candidate 1 supplied the continuous header/title; candidate 2 supplied the more consistent English raster lettering and stepped tabs. Both remained donor images, not the final Assembly. |

## Why the first four passes did not fix it

The failure is not prompt quality. It is a category error: the chrome —
window frame, title-bar glass, tab notches, the checkbox frame and its blurred
interior, the tick, the bead, the ✕ button, the dropdown triangle — is a set of
**fixed sprites that already exist as pixels** in the Reference Screen. Asking a
diffusion model to redraw a two-pixel stroke and a stair-stepped tab notch from
a verbal description yields a confident approximation every time, and sharpening
the description only makes the approximation more confident. Each pass moved the
error around rather than removing it.

`CONTEXT.md` already draws the line this run crossed: a **Render Pass** is
probabilistic, **Assembly** is deterministic placement of approved assets. Chrome
belongs to Assembly. Generation is the right tool for a *new* object that does
not exist yet (the golf club in `golf-club-object-v002`); it is the wrong tool
for reproducing artwork already in hand.

The owner's final review identified three remaining Assembly errors rather than
requesting another full redraw: the top header and its blue alignment, the
hard-thresholded English lettering, and the `object` / `material` tabs.  v005
therefore treated Assembly v001 as reference image 1 and requested an edit in
place.  Assembly v002 registers the two resulting donors to the baseline frame
and accepts their pixels only through explicit header, lettering and tab masks.
The search-field edge, dropdown, body checkboxes, checkbox states, layout,
border and crop remain Assembly v001 pixels outside those masks.

The resulting Fidelity Check reports zero changed pixels and zero maximum
channel error outside the declared mask.  That establishes strict preservation;
human visual approval still decides whether the repaired regions are accepted.

## Rule taken from this

Before spending on a Render Pass, ask whether the pixels being requested already
exist in the Reference Screen. If they do, cut them and composite; generate only
what is genuinely absent. A brief that has to *describe* existing artwork in
prose is a signal the work belongs in Assembly.

## Cost

10 completed images across five passes, estimated ~$0.50, OpenRouter
`qwen/qwen-image-3-pro`. Prompt IDs `50a9a535…`, `2b10f2a9…`,
`a3b37948…`, `4ea11b1d…`, `a1d11885…`. OpenRouter usage was not exposed
for v005, so its ~$0.10 remains an estimate rather than an actual charge.

An earlier request (`4631a450…`, 4 images) was destroyed by an unrelated pool
restart and reconciled as possibly-spent; see
`artifacts/runs/museum-filter-retro-skin-v001/reconciliation.json`.
Including that unresolved request, the Issue records 14 requested, 10 completed
and 4 ambiguous outputs.  This run supports milestone prototype #111, so the
owner's 200-generation milestone cap supersedes ADR 0003's ordinary per-Issue
ceiling; all 14 are carried into the milestone ledger.
