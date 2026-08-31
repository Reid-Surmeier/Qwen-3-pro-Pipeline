VERDICT: SHIP

Independent adversarial review of the candidate against the reference. All nine
region pairs were read at magnification, and every claim below is backed by
pixel measurement on `pair-full.png` (reference = rows 0–484, candidate =
rows 495–979, both 1001x485). Coordinates are given in **map pixels**
(x = 0..1000 left→right, y = 0..484 top→bottom of each half); the magenta
overlay in the region crops is one line per 10 map pixels, so x=120 is the 12th
magenta column, y=340 the 34th magenta row.

No blockers were found. Five findings, all minor or cosmetic.

---

## Findings

### 1. Marquesas container box deleted outright — MINOR
- **File:** `pair-full.png` (candidate half, Pacific at left, immediately below
  the "Marquesas" label). Not covered by any region crop.
- **Location:** map x 120–134, y 331–347 (magenta columns 12–13.5, rows 33–35).
- **What is wrong:** The reference draws a grey-framed box there filled solid
  green. The candidate removes the frame *and* the fill, leaving bare white. The
  licence names Marquesas among the neutral grey container boxes that are base
  map and must stay. Measured: 188 px of reference fill with 0 % candidate
  coverage, and the surrounding grey frame is gone (no grey of any shade within
  2 px of the old frame).
- **Collateral:** the reference's grey zone-joint line runs down x=120; the
  candidate correctly lightens it to pale grey above y=330 and below y=348 but
  leaves a 16-row white gap (y 331–347) where the box used to be.
- **Why not a blocker:** the reference box is a *solid colour swatch*, built
  exactly like the zone-marker boxes at x 691–697 / x 745–752 / x 743–755 that
  the licence does order removed. Under that reading the removal is licensed and
  only the frame is at issue. Ambiguous, so scored minor rather than blocker.

### 2. Lat/long grid segments recoloured with a country fill — COSMETIC
- **Files:** `pair-full.png`; the largest instance also falls inside
  `pair-north-america.png` (candidate panel, lower right, west of Central
  America).
- **Locations:** 41 specks totalling 81 px where a reference grid line over open
  sea is painted a palette fill colour. Largest: x=300, y 272–280 (pink, 8 px,
  E Pacific); x=920, y 291–298 (7 px); x 79–83, y 306–309 (6 px); x=120,
  y 348–367 (red, 1 px wide, beside French Polynesia).
- **What is wrong:** a land colour bleeding along a grid line in open ocean.
  Every instance is 1 px wide and ≤ 8 px long; none reads as land at scale.

### 3. Micro-island detail thinned — COSMETIC / MINOR
- **Files:** `pair-north-america.png` (far lower-right, Lesser Antilles);
  `pair-full.png` (French Polynesia / Tonga / Samoa);
  `pair-australia.png` (far right edge, New Caledonia / Vanuatu).
- **Locations:** Lesser Antilles x 331–341, y 266–273 — reference has ~8 islands
  of 1–2 px, candidate retains 3. French Polynesia x 100–140, y 350–367 — the
  black outline pixels around the 1-px islands are dropped and several island
  pixels with them. New Caledonia / Vanuatu x 945–950, y 369–373 — reference has
  ~12 px of land, candidate 2.
- **What is wrong:** loss of sub-pixel-scale island ink. Nothing recognisable as
  a named landmass is lost; every reference land component ≥ 8 px outside plate
  footprints survives (verified by component-wise coverage test).

### 4. Reconstruction gaps under removed plates — COSMETIC (explicitly licensed)
- **Files:** `pair-great-britain.png`, `pair-australia.png`,
  `pair-north-america.png`.
- **Locations:** southern England/Wales, x 470–496, y 163–171 — the candidate's
  coast stops ~2 rows short of where the reference's coast resumes below the old
  "DST 09:01PM" plate, leaving a thin white notch across the Channel. Short
  breaks in the pale-grey zone-joint lines where plates crossed them, e.g.
  x=920, y 373–375.
- **What is wrong:** nothing beyond what rule 4 permits ("thinner/dashed/paler
  or small white notches"). Recorded for completeness only.

### 5. Island-group marker boxes removed with no substitute — INFORMATIONAL
- **Files:** `pair-asia.png` (candidate panel, south of India),
  `pair-se-asia.png`.
- **Locations:** Andaman/Nicobar marker x 745–752, y 275–295; Maldives marker
  x 691–697, y 279–286; Cocos marker x 743–755, y 334–346.
- **What is wrong:** nothing under the licence — these are grey-framed flat
  colour marker boxes and their removal is required. Noted only because they
  were those groups' only depiction, so the candidate map has no islands there.

### 6. Northern Ireland takes Ireland's colour, not the UK's — COSMETIC
- **File:** `pair-great-britain.png` (candidate panel, left of Great Britain).
- **Location:** x 471–484, y 149–162.
- **What is wrong:** Ireland is lavender and Great Britain cyan; Northern
  Ireland is inside the lavender blob. At 1 map px per ~7 km the two are a
  single shape in the reference too, so this is not separable at this scale.

---

## Verified clean (evidence)

1. **Flat fills, no dithering.** Candidate uses 44 distinct colours against the
   reference's 247; the map body is exactly 10 palette fills plus the grid
   lavender and the copyright green.
2. **No adjacent country shares a colour.** Region-level test over all 11 fill
   colours (connected components ≥ 120 px, 3-px mutual dilation, sea-gap
   filtered) returned 2 candidate pairs, both ≤ 28 px; both were inspected
   pixel-by-pixel and are a corner approach across two intervening countries
   (x≈505, y≈291) and one country re-joined after a border line (x≈535, y≈321).
   Zero genuine violations.
3. **All annotations gone.** DST yellow (252,254,4) = **0 px**. Date-line orange
   (252,102,4) = **0 px**. Plate green (4,254,84) = **0 px**. Plate pink
   (247,124,124) = **0 px**. Corner date/time boxes, UTC boxes, the Greenwich
   bar and its vertical caption, and the date-line rules all removed (every lost
   grey component sits at exactly those coordinates).
4. **No annotation remnants.** Candidate dark ink that is not within 2 px of
   reference dark ink totals **18 pixels** image-wide, largest component 3 px.
   No frames, digits, bars or glyph fragments survive anywhere. Spot-checked the
   17 auto-detected plate footprints: all show zero residual ink except the
   copyright box, which is meant to stay.
5. **Copyright box kept intact.** The green box at x 45–200, y 448–482 is
   pixel-identical to the reference apart from one stray 1-px annotation rule at
   its right edge.
6. **Every city/place label intact.** The navy label mask (4,2,52) is
   **pixel-identical**: 5171 px in both halves, XOR = 0. No label is damaged,
   moved, or dropped. GREENLAND / ALASKA / CHINA / NEPAL / INDIA / KAMCHATKA /
   NEW ZEALAND are base-map navy labels and are correctly preserved.
7. **No sea painted as land.** Candidate fill over reference white totals
   **307 px** in 92 components, largest **16 px**. Nothing at scale.
8. **No land erased.** Every reference-fill → candidate-white component ≥ 100 px
   is a 43x9 plate footprint. Land-pixel ratio candidate/reference (plates
   excluded): world 1.07, North America 1.06, South America 0.97, Africa 1.07,
   Europe 1.13, N Asia 1.09, Australia 1.13, Greenland 1.14, Antarctic edge
   0.90. No landmass moved, cut, fused or shrunk.
9. **Grey zone joints lightened.** 10,629 px of pale grey (184,184,184)
   introduced; dark grey (100,102,100) falls 14,222 → 1,721, the remainder being
   the retained neutral container frames.
10. **Container boxes retained** at Iceland, Socotra, the Caribbean and the
    Norfolk-area box (x 945–953, y 389–395) — all still framed in grey.
11. **Reconstruction verified by hand** under the removed plates at Great
    Britain, the Mongolia/China border (x 762–808, y 177–189 — clean two-country
    reconstruction with the border redrawn), Australia (whole continent, one
    flat blue, coastline and Tasmania intact), Venezuela/Colombia under the
    Caracas plate, and West Africa under the Greenwich bar.
12. **Multi-zone countries correctly unified**: Russia, Canada, the USA,
    Australia, Brazil, China and Indonesia each collapse from several reference
    zone colours to one flat country colour.
