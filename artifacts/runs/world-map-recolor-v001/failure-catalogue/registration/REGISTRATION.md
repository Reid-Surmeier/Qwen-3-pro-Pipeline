# Local registration of the NE cid layer to the source frame (research ticket #146, map #140)

Facts and artifacts only. Question (issue #146): can the NE cid grid be registered to the
source raster with verified residual <=2 px, region by region — and where can it not?

**Answer: yes for the great majority of coastline-verified land.** After a two-iteration
locally-measured warp, every continent-scale region except Greenland reaches p90 residual
<=1.3 px over its reliable tiles. Not registrable to <=2 px: far-north Greenland, the Arctic
fringe (y<~32), New Zealand, the Pacific island fields, and sparse-island tiles generally —
patch-vote only there under the #143 rule.

Sources: `assembly/wtz-map-12map-1001x485.gif` (source raster, 1001x485),
`assembly/countries-raw.npy` (pre-dilation cid grid from `country_layer.py`'s global
Mercator+cubic fit), `assembly/plates-mask.png`, the FILLS colour list in
`assembly/compose_v3.py`, `../BLINDSPOTS.md` (#142's 10-50 px finding), and the outputs of
`make_registration.py` / `make_reg_crops.py` in this directory (fully deterministic, $0).

## Method

- **Source land** = union of the 14 exact FILLS colours (minus plate rectangles from
  `plates-mask.png` and the credit box) ∪ black border components touching a fill,
  closed 5x5 and hole-filled so enclosed white-fill countries count as land (146,333 px;
  cid raw land 147,027 px). Annotation regions (plates dilated 2 px, credit box, 4-px frame)
  are excluded from all matching as don't-care pixels.
- **Block matching**: 64x64 tiles, stride 32 (50 % overlap), search ±60 px. Score per shift =
  (land∩land + water∩water)/valid-px (FFT correlation); recorded per tile: peak agreement,
  land-overlap ratio at peak, second-peak margin (peak minus best score >5 px away),
  sub-pixel parabolic refinement. **Reliable tile** = margin >=0.010, peak >=0.80,
  overlap >=0.5, land >=600 px, peak not at the search edge.
- **Field**: reliable tile shifts, neighbour-median outlier rejection (>12 px deviation from
  the median of neighbours within 120 px, isolated tiles dropped), linear scattered
  interpolation + nearest fill, Gaussian smoothing sigma=16. Second iteration: re-measure the
  warped grid (±25 px) and add the incremental field. Warp is a reverse map with
  nearest-neighbour sampling, so ids stay integral.
- **Residual AFTER** is measured by the identical matcher on `countries-registered.npy`,
  with search restricted to ±15 px so along-coast ridge slides cannot fake large residuals
  (anything worse would surface as an edge/unreliable tile, and none did outside the
  flagged regions).

## Residual per region (px, reliable tiles; med/p90/max = |shift| magnitude)

| Region | tiles | reliable | BEFORE med | p90 | max | AFTER med | p90 | max | verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| N America | 51 | 31 | 3.71 | 10.82 | 26.1 | 0.62 | 1.28 | 6.4* | **<=2 px verified**\* |
| Greenland | 12 | 10 | 8.45 | 21.31 | 28.25 | 0.84 | 6.35 | 6.35 | **NOT verified** (north) |
| C America/Caribbean | 11 | 8 | 3.11 | 9.33 | 9.33 | 0.20 | 0.36 | 0.36 | **<=2 px verified** |
| S America | 19 | 9 | 10.78 | 22.09 | 22.09 | 0.21 | 0.25 | 1.34 | **<=2 px verified** |
| Europe | 17 | 14 | 1.02 | 28.55 | 75.27† | 0.31 | 0.60 | 0.77 | **<=2 px verified** |
| Great Britain/Ireland | 3 | 1 | 0.73 | — | — | 0.31 | — | — | **<=2 px verified** (n=1 + crop) |
| Africa | 35 | 18 | 3.68 | 11.50 | 12.98 | 0.26 | 0.48 | 0.60 | **<=2 px verified** |
| Arabia/Middle East | 12 | 4 | 0.93 | 2.35 | 2.35 | 0.19 | 0.48 | 0.48 | **<=2 px verified** |
| Russia/N Asia | 62 | 23 | 8.74 | 14.27 | 28.55 | 0.63 | 1.20 | 1.53 | **<=2 px verified** |
| S/E Asia | 28 | 17 | 2.35 | 7.86 | 7.89 | 0.24 | 0.59 | 1.16 | **<=2 px verified** |
| SE Asia/Indonesia | 11 | 8 | 7.47 | 10.70 | 10.70 | 0.19 | 1.16 | 1.16 | **<=2 px verified** (mainland) |
| Australia | 13 | 9 | 14.97 | 17.38 | 17.38 | 0.26 | 0.68 | 0.81 | **<=2 px verified** |
| Australia SW | 5 | 4 | 14.97 | 17.37 | 17.37 | 0.16 | 0.68 | 0.68 | **<=2 px verified** |
| New Zealand | 0 | 0 | — | — | — | — | — | — | **unmatchable** (sparse) |
| Pacific islands | 0 | 0 | — | — | — | — | — | — | **unmatchable** (sparse) |

\* N America's AFTER max 6.4 is tile (224,160), an interior tile with land-overlap 1.000 at
the "peak" and margin 0.0103 — a fully-land tile sliding inside the continent, i.e. an
aperture artifact, not a coast mismatch. Its coastline-bearing neighbours are all <=1.3 px.
† Europe's BEFORE max 75.27 is tile (480,64), a low-margin (0.012) false peak in the
Norwegian-Sea tile; it was rejected by the neighbour-median filter and never steered the field.

Whole-map headline (source fill px outside cid land, excluding plates/credit; #142 quoted
~10.6 %): outside raw grid 15,245 px = 14.05 %, of which 8.59 % lies >2 px from any cid
land; outside the registered grid 6,465 px = 5.96 %, of which **3.09 % lies >2 px** — and
that remainder is dominated by fill-coloured ocean markers (Hawaii/Kiribati/Polynesia dots)
and small islands the NE grid does not carry at this scale.

## Worst pre-correction tiles (quantifying #142's 10-50 px finding)

The displacement is systematic, not noise (see `displacement-field.png`): the cid layer must
move **south by 15-24 px across Australia, S America's south, S Africa and the Arctic rim**,
with the interior near 0 — a north-south stretch the global Mercator+cubic fit could not
represent. Largest trusted tile shifts (x,y = tile origin): (544,96) Scandinavia
dx-7.0/dy+27.7 · (416,0) Arctic dy+28.1 · (288,160) US east coast dx-15.9/dy+20.7 (ridge-
slide component along the seaboard) · (320,384)(288,384)(288,416) southern S America
dy+21.8-21.9 · (320,0)(320,32) Arctic Canada dy+20.1-21.2 · (864,384)(832,384) Australia
dy+17.2 · (704,0)(736,0) Arctic Russia dy+22.2-23.8.

## Verdict under decision #143 (per-pixel cid only where residual verified <=2 px)

**Per-pixel cid allowed** (coastline-verified, AFTER p90 <=1.3 px): N America (south of the
Arctic fringe), C America/Caribbean mainland, S America, Europe incl. GB/Ireland, Africa,
Arabia/Middle East, Russia/N Asia (south of the Arctic fringe), S/E Asia, SE Asia/Indonesia
mainland+large islands, Australia (SW included), southern Greenland tiles (median 0.84).

**Patch-vote only** (residual >2 px or unverifiable):
1. Greenland's north half — pre-shift gradient 8→28 px across the island; a residual
   6.3 px tile (384,0) survives both iterations.
2. Arctic fringe, y < ~32 map-wide — land overlap only 0.5-0.7 even at peak: the source
   draws the Arctic archipelagos structurally differently from Natural Earth.
3. New Zealand and all Pacific island fields — zero reliable tiles; the source marks many
   of these as dot markers that are not NE land at all.
4. Any sparse tile (<600 cid land px; 42 tiles) — small Caribbean/Atlantic/Mediterranean/
   Indonesian-fringe islands: the matcher's peak is not trustworthy there.
5. Outside the reliable-tile hull (map edges) the field is extrapolation (red rims in
   `displacement-field.png`) — unverified by construction.

Caveat: verification is coastline-anchored. Fully-interior tiles carry no local signal
(aperture problem); they inherit the interpolated field. Internal country borders in
continent interiors are therefore *consistent* with the coasts but not independently
verified to <=2 px.

## Visual confirmation (gridded 4x crops, cyan = raw grid outline, magenta = registered)

- `reg-australia-sw.png` — raw outline floats ~17 px north (cyan ring off the north coast);
  the magenta outline hugs the source's west coast, Bight and Tasmania. Read and confirmed.
- `reg-great-britain.png` — raw cyan sits east of Britain; magenta traces the green Britain
  and Ireland shapes. Read and confirmed.
- `reg-arabia.png` — magenta follows the Red Sea coast, Gulf and Horn; cyan doubling
  visible 3-6 px off along the Red Sea corridor. Read and confirmed.

## Artifacts (this directory)

`countries-registered.npy` (int16 ids, -1 water; warped countries-raw, ids verified a
subset of the raw ids) · `displacement-field.npz` (dense dy/dx float32 + reliable tile
table) · `displacement-field.png` · `residuals.json` (full per-tile before/after tables +
region summaries + parameters) · `make_registration.py`, `make_reg_crops.py` (reproducers;
run from `assembly/`) · the three `reg-*.png` crops.

Note for consumers: `countries-registered.npy` is warped from **countries-raw**; re-apply
the dilation step from `country_layer.py` downstream if the dilated variant is needed.
