# Re-skinning a museum filter panel as an RO-style options window

Issue [#118](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/118).
Reference Screen: `artifacts/references/museum-filter-retro-skin-v001/style-ro-options-window.png`
(SHA-256 `7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16`).

## Outcome

**Four full-redraw Render Passes failed to reach the required fidelity, so the
work moved to Assembly. A final two-output Qwen edit pass helped diagnose the
remaining defects, but Assembly v002 was rejected because rectangular masks
imported its backgrounds. Assembly v003 was also rejected because it changed
the complete English layer and still did not integrate three marked regions.
Assembly v004 returns to v001 and changes only those regions with native-scale
foreground and repair masks.**

## What each pass got wrong

| Pass | Change | Owner's verdict |
| --- | --- | --- |
| v001 | Two references, style + data card, 2:3 portrait | Layout came from the data card, not the style window. Modern sans. Slider thumb sat on the left arrowhead. |
| v002 | Dropped the data reference; layout copied the BGM/Effect row order, 16:9 | Over-corrected — slavishly copied the reference's row order. Text off, everything cramped, colour drift. |
| v003 | Any/All became two checkboxes, 4:5, palette pinned to sampled hexes | Size right. Font still too thick. Tabs wrong. Checkboxes not exact. Title misaligned. ✕ button wrong. |
| v004 | Second reference: a 2–4× magnified parts sheet cut from the original | Closer on every axis, still not the original's chrome. |
| v005 | Assembly v001 became the composition authority; the original and parts sheet became style authorities; 3:2 final edit | Candidate 1 supplied the continuous header/title; candidate 2 supplied the more consistent English raster lettering and stepped tabs. Both remained donor images, not the final Assembly. |

## Assembly v003 correction

The owner identified v002's remaining defect as Assembly, not generation:
rectangles around the title, labels, material rows, and tabs carried Qwen's
slightly different blue, white, and lavender backgrounds into the final image.
The objective outside-mask score was true but insufficient because the declared
mask itself owned far more background than the actual foreground change.

Assembly v003 therefore returns to the 313×211 Assembly v001 native image. It
predeclares a permitted mask from the old exact-ink glyph pixels and new
PixelMplus glyph silhouettes, restores only the old text pixels from
Assembly-v001-owned backgrounds, and renders the exact strings through that
mask. The title-bar gradient, right bead, close button, tab silhouettes,
controls, frame, crop, and every other background pixel remain Assembly v001
pixels. The result is enlarged 4× with nearest-neighbour resampling; no new
Render Pass ran and no v005 raster enters the final Assembly.

The v003 mask is declared before composition and contains 4,831 native pixels
(77,296 review-scale pixels). The actual difference is a strict 4,207-pixel
native subset (67,312 review-scale pixels), with zero changes and zero maximum
channel error outside the declaration. Every individual edit box is 36.5%
filled or less, rather than being a solid background patch. The right header
controls are byte-identical to Assembly v001, and full/native visual readback
found all 19 Exact Copy entries present.

The owner rejected that broader correction: v001's English was the stronger
source, while the left bead, right bead/close cluster, and inactive material tab
still showed rectangular donor backgrounds or an unintegrated silhouette.

## Assembly v004 three-region correction

Assembly v004 starts from Assembly v001, not v003. It leaves the complete
English layer, active object tab, body, controls, layout, frame, crop, and every
other unmarked pixel byte-identical to v001. No Qwen or other generation ran.

The two 13×13 bead regions and the 19×19 close-button region first recover the
same resampled title glass used to build v001, then reapply only elliptical or
button-shaped foreground pixels from the original sprites. This removes the
captured square blue/cyan backgrounds, including the cyan strip at the far
right. The inactive material tab first recovers the correctly phased v001 body
stripes, adds a source-like stepped silhouette, and finally restores the exact
v001 `material` ink pixels.

The declared v004 edit mask is the exact baseline-to-candidate difference: 404
native pixels, all within the three marked regions. The actual change and the
declared mask are byte-identical; zero pixels change outside it. The full-size
candidate and enlarged before/after crops are recorded in
`artifacts/runs/museum-filter-assembly-v004/contact-sheet.png`. This is machine
verification of scope and integration, not the owner's subjective approval.

The owner accepted the direction but rejected v004 as final because the tight
13px masks visibly clipped both beads, the material-tab stair profile ran in
the opposite direction, and the `material` copy sat against the tab edge.

## Assembly v005 bead and tab geometry correction

Assembly v005 again starts from v001. Each bead is recut from a padded 64×64
region in the full-resolution Reference Screen and downsampled into a 15×15
native asset whose alpha mask has a guaranteed empty pixel on every side. This
keeps the soft circular edge complete without restoring a square donor patch.
The close button keeps v004's foreground-only correction.

The inactive tab grows from 16 to 20 native pixels wide. Its source-like stairs
now run from wide top and bottom tips to a narrower middle, reversing v004's
profile. The exact v001 `material` bitmap is moved two native pixels inward;
its rightmost glyph pixel has three clear pixels before the middle border.

The v005 declared mask exactly equals the actual baseline-to-candidate
difference: 696 native pixels, all inside the same three semantic regions, with
zero changes outside. The complete English/body/control layer outside the
marked material-tab copy remains byte-identical to v001. No generation ran.

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

The v002 Fidelity Check reported zero changed pixels outside its rectangles,
but that did not prove the rectangles were correctly owned. The first v003
attempt still derived its mask from the completed output, which made that proof
circular. The corrected v003 declares old and new glyph silhouettes first, then
proves the completed output is a subset. Human visual approval still decides
whether the repaired regions are accepted.

## Rule taken from this

Before spending on a Render Pass, ask whether the pixels being requested already
exist in the Reference Screen. If they do, cut them and composite; generate only
what is genuinely absent. A brief that has to *describe* existing artwork in
prose is a signal the work belongs in Assembly.

An edit mask must express source ownership, not merely contain a change. A
rectangle around text can pass outside-mask identity while still importing an
incorrect background. For flat interface bands and labels, restore the
authoritative background first and composite only the foreground silhouette.

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
