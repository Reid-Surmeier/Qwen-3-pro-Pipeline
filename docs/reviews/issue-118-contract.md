# Issue 118 blind-review contract

Review the candidate at `artifacts/runs/museum-filter-assembly-v002/assembly-v002.png`
against the hash-locked Assembly v001 baseline and old-game source window.  This
is a static visual artifact; no interactive behavior is in scope.

## Acceptance clauses

1. **C1 — Composition preservation.** The candidate keeps Assembly v001's
   1252×844 dimensions, landscape silhouette, crop, outer magenta/white frame,
   panel geometry, search field, dropdown, checkbox positions and states,
   material row order, spacing and bottom stripe band.
2. **C2 — Header repair.** The title bar is one continuous, level pale-blue
   glass band with aligned top and bottom edges and no cyan block, vertical blue
   seam, height step or disconnected patch beside the right bead and close
   button. `Object type / material` is vertically balanced with blue visible
   above and below.
3. **C3 — Lettering repair and Exact Copy.** English lettering retains an
   intentional low-resolution raster character but is consistent and legible,
   without the baseline's malformed hard-threshold spikes, merged glyphs or
   uneven baselines. Every visible string, comma, parenthesis and number matches:
   `Object type / material`; `object`; `material`; both instances of `Search`;
   `Match`; `Any`; `All`; `selected filters.`; `Metal (5,001)`;
   `Paper (3,652)`; `Glass (3,182)`; `Drawings (2,606)`;
   `Graphite (2,443)`; `Paintings (2,395)`; `Vessels (2,074)`;
   `Watercolors (1,962)`; `Wood (1,899)`; `Dishes (1,837)`.
4. **C4 — Tab repair.** `object` remains the active upper tab and `material`
   remains the inactive lower tab. Both read bottom-to-top, remain narrow and
   centered, and the inactive tab has the source-like stepped notch while the
   active tab stays white and flush without a surrounding box.
5. **C5 — Control integrity.** The search-field edge, dropdown, body checkbox
   artwork, one-ticked/eleven-empty states, outer frame, panel and material grid
   do not acquire donor drift or new controls.
6. **C6 — Declared edit mask.** The candidate may differ from Assembly v001
   only inside the supplied edit mask. Any changed pixel outside it is a
   blocking failure.

## Evidence to inspect

- `artifacts/runs/museum-filter-assembly-v002/contact-sheet.png`
- `artifacts/runs/museum-filter-assembly-v002/assembly-v002.png`
- `artifacts/runs/museum-filter-assembly-v002/assembly-v002-native.png`
- `artifacts/runs/museum-filter-assembly-v002/edit-mask.png`
- `artifacts/runs/museum-filter-assembly-v002/verification.json`

PASS means no clause violation was found in the named candidate SHA. It is
evidence for, not a substitute for, the owner's final visual approval.
