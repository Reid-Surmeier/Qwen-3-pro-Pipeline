# Why the mechanical gates are blind — reconciliation + checklist (research ticket #142, map #140)

Facts only. Sources: my own pixel probes of `final-v011-assembly.png` (byte-identical to
`assembly/assembled-v3.png` — verified) against `assembly/wtz-map-12map-1001x485.gif`, the cid grids
(`assembly/countries.npy`, `assembly/country-names.json`), the gate source
(`assembly/compose_v3.py` lines 875–926), `assembly/fidelity-report-v3.json`, `ledger.md`, and the
gridded reconciliation crops in this directory (`recon-*.png`, magenta 10-px gridlines labelled with
native 1001x485 coordinates, identical box and grid on both halves).

## Part 1 — Reconciling the disputed catalogue rows

The dispute is real and both sides measured true things **in different coordinate frames**. The
build's probes sample in **cid space** (the Natural-Earth projected grid that also painted the
layer); the catalogue's reviewer read the image in **source-raster space** (where the GIF draws the
countries). The projected grid is misregistered against the source drawing by roughly 10–50 px
depending on region — measured directly: 22.5 % of Australia's cid footprint and 36 % of the UK's is
white ocean **in the source**; globally 10.6 % of source fill pixels fall outside cid land. So a
probe over the cid mask can read "painted solid" while the country the source drew sits erased a few
tens of pixels away.

| Catalogue claim | Verdict | Honest v011 state (source frame, `recon-*.png`) |
| --- | --- | --- |
| GB "erased except one cyan crumb" | **Half stands** | The source's green Britain (~x455–485) *is* erased. But the replacement is not one crumb: a 366-px cyan Britain is painted at x477–519/y119–164, ~20 px east of the source drawing, thinner and fragmentary, with a lavender displaced Ireland beside it. Failure class: **displacement + shape degradation**, not pure erasure. ("One cyan crumb" was an interpretation error.) |
| Italy's boot "absent" | **Half stands** | No boot silhouette is readable — TRUE. But Italy is not unpainted: 487 of its 635 cid px are solid yellow FCCE34; the boot is unreadable because the shape is destroyed and the surrounding Mediterranean is painted with salmon/green confetti (sea as land). Failure class: **shape destruction + sea-painted-as-land**, not erasure. |
| Arabian peninsula "unpainted white, green/black debris band in the Red Sea" | **Mostly wrong** | The peninsula is painted: 1192/1353 cid px solid mint 94F7C6 (the build probe was correct), and in the source-frame window x585–660/y225–290 the v011 white count (706) is *lower* than the source's own (865). The "debris band" is misregistered paint: a doubled black coastline squiggle along the Red Sea corridor plus pale-green CCFE9C spill (316 px) and 110 black px in x585–605/y250–305, with small red cross debris and white gouges inside the mint fill. Failure class: **off-palette recolour + doubled/misregistered coastline debris**, not an unpainted peninsula. |
| Australia "displaced ~11 px north / SW coast missing" | **Stands — understated** | Land centroid moved 11.8 px north (375.8 → 364.0 in the x770–930 window). At Perth's latitude the source coast starts at x758–760 (rows y385–400) while the v011 blue fill starts at ~x805–809: **~47 px of Western Australia missing**, not the ~20 the catalogue stated. Three source zone fills replaced by one blue; misregistered black coastline drawn inside the fill; Perth label half-erased. |

Row-probe transcript (Perth latitudes, ink = non-white/non-grid):
`y=385 src x[758,926] v011 x[807,926] · y=390 src x[758,920] v011 x[806,920] · y=395 src x[759,920] v011 x[809,908] · y=400 src x[760,929] v011 x[780(label "P"),898]`.

Corrections the catalogue needs: GB/Italy/Arabia rows should be re-classed from "erased/unpainted"
to "displaced / shape-destroyed / off-palette with debris"; Australia's missing-coast figure should
read ~47 px, not ~20. Everything else in those rows reproduced.

## Part 2 — Why each gate is blind (from the gate source, compose_v3.py:875–926)

**Fidelity gate** (`outside = changed & ~declared; pass iff outside.sum()==0`):
- `declared` covers **211,501 px = 43.6 % of the canvas** (fidelity-report-v3.json). Every pixel
  inside it may take *any* value and still pass. All paint, all debris, all erasure happened inside.
- It only proves *containment* of change, never *correctness* of change. It is a "did we scribble
  outside the lines we drew ourselves" check, and the lines are self-declared.

**SPOT** (majority palette colour over cid mask == assigned colour, 75 named countries):
1. **Samples in the same cid grid that painted the layer** — self-referential. Projection-vs-source
   misregistration (the dominant failure, catalogue #30) is invisible by construction.
2. **Majority vote ignores coverage** — 88 % or 8 % painted both pass; "unpainted" fires only at
   exactly zero palette pixels.
3. **Filters to its own palette first** (`pal_lookup`) — off-palette debris and wrong-colour pixels
   are excluded from the vote instead of failing it.
4. **Tests its own assignment, not the spec** — `want = PALETTE[colour_idx[ci]]`: the 31-colour
   pastel scheme passes because the check's ground truth *is* that scheme, not the source's ~10-fill
   palette.
5. **Coverage gaps** — United Kingdom and Italy are not in the 75-name list; no micro-country is.
6. No shape, position, topology, coastline, or connected-component test of any kind.
7. No label test of any kind (anchoring, legibility, glyph retention).
8. No sea-is-sea test — painting ocean as land passes both gates.
9. No palette census or contrast test (18 flat colours >200 px vs the source's ~10; navy-on-red
   ":ND:A" passes).
10. No cross-version regression test — v009's label wipes re-passed identical gates in v010/v011.
11. No check of the delivered artifact — gates run on `assembled-v3.png`; that it equals
    `final-v011-assembly.png` here is verified luck, not a gate; nothing checks the FigJam render.

Ledger rows for v008–v011 all say "fidelity outside_changed=0; spot checks 75/75" while catalogue
items #16, #26, #28, #30, #31, #32 were present in the shipped image. Both statements are true;
the gates simply do not measure what the failures are made of.

## Part 3 — THE CHECKLIST for a visual-review gate

One line per blind spot; each is a checkable visual assertion against the SOURCE raster frame.

1. **Coastline correspondence:** every coastline pixel run in the source has a counterpart within
   N px (N≤3) in the candidate, and vice versa — both directions, per connected component.
2. **Registration:** per continent/region, the land-mask centroid and bounding box differ from the
   source's by ≤2 px; no whole-shape translation (Australia: 11.8 px would fail).
3. **Coverage in source frame:** ≥98 % of source land-fill pixels carry a flat land colour in the
   candidate, measured over the *source's* drawn land, never over the projection's own mask.
4. **Sea stays sea:** ≤0.5 % of source ocean/white pixels carry a land colour in the candidate
   (Java Sea, Mediterranean confetti, Persian Gulf spill would fail).
5. **Shape identity:** each named landmass in the candidate is recognisable against the source at
   4x by silhouette IoU ≥0.9 per country above 100 px (GB, Italy, WA would fail).
6. **Component count:** connected land components per region match the source ±1 (no fusion —
   Indonesia+Malaysia; no fragmentation — Philippines).
7. **Palette membership:** every flat fill colour in the candidate is a member of the agreed
   palette, and the count of distinct flat colours matches the palette size exactly.
8. **Colour audit is exclusion-free:** off-palette pixels count as failures, never get filtered out
   before the vote.
9. **Label anchoring:** every label/city-dot sits on or within 2 px of its own country's land fill
   in the candidate (New York, Dakar, Lima, Dubai would fail).
10. **Label integrity:** per label box, ≥90 % of the source's glyph pixels survive
    (Perth 14/48, Paris 16/171, London 47/168 would fail).
11. **Label contrast:** every glyph's colour differs from its local background by a readable margin
    (WCAG-ish luminance delta; navy-on-red ":ND:A" would fail).
12. **No debris:** zero connected non-palette components >3 px outside declared label/plate sites
    (Cape Verde blobs, red crosses, doubled coastlines would fail).
13. **No interior strokes:** no dark outline runs inside a flat fill that have no counterpart stroke
    in the source (Australia's inner squiggle would fail).
14. **Cross-version stability:** every region that passed review in version k is pixel-identical or
    explicitly re-declared in version k+1 (v009 Perth wipe would fail v010).
15. **Deliverable identity:** the reviewed image, the gated image, and the published render (file
    and FigJam node) are byte- or hash-identical.
16. **Frame declaration:** every mechanical probe states which coordinate frame it samples in, and
    at least one assertion per country runs in the source-raster frame.

## Unverifiable / caveats

- The 42.9 % of cid land not covered by source fills overstates misregistration alone: the source
  legitimately leaves some countries white and draws labels/plates over land. The reverse number
  (10.6 % of source fills outside cid land) is the cleaner misregistration signal.
- I did not re-review v007–v010; the gate-blindness analysis is from the v3 gate source, which per
  ledger.md ran unchanged for v008–v011.
- "Would fail" annotations in the checklist are asserted from the v011 measurements above, not from
  running an implemented gate.

Regenerate the recon crops: `python3` snippet embedded in the #142 work log; boxes:
GB (440,110,530,180) 6x · Italy (495,160,570,225) 6x · Arabia (570,215,670,310) 6x ·
Australia (750,330,940,430) 4x. Grid: magenta lines every 10 native px, labelled.
