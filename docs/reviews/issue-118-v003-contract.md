# Issue #118 Assembly v003 blind-review contract

Candidate: `90af97002816d0f68af9a48bacedf2650a73d629`

Review the candidate at both 1252×844 and native 313×211. Assembly v001 is
the background and control authority. Assembly v002 is rejected evidence of
the rectangular-background defect and must not be treated as an authority.

## Clauses

- **C1 — Composition preservation.** The candidate keeps Assembly v001's
  dimensions, crop, magenta/white frame, panel geometry, controls, checkbox
  states, row order, spacing, and bottom stripe band.
- **C2 — Header ownership.** The blue title-bar glass, its gradient and rules,
  the right bead/dot position, and the close button match Assembly v001. Only
  foreground-shaped title glyph pixels may differ; no rectangular blue patch,
  cyan seam, stepped gradient, or shifted right bead is present.
- **C3 — Shape-aware Assembly.** The edit mask follows actual title, label,
  count, and tab-glyph pixels. It contains no solid enclosing rectangle and is
  exactly equal to the RGB changed-pixel mask. Every per-box fill fraction is
  at most 0.37.
- **C4 — Exact and legible copy.** All 19 strings in `run.json` are present
  character-for-character. At full and native scale the text is readable and
  has no visibly broken, merged, doubled, clipped, or haloed glyphs and no
  mismatched white/pink background patch around it.
- **C5 — Tabs.** `object` remains the active upper tab and `material` remains
  the inactive lower tab. Assembly v001's tab silhouettes, fills, stepped
  inactive notch, edges, positions, and orientation are retained; only their
  foreground glyph pixels change.
- **C6 — Deterministic evidence.** The right header controls are byte-identical
  to Assembly v001. The candidate has 6,197 changed native pixels, zero changed
  pixels outside the actual-difference mask, and zero maximum outside-mask
  channel error. No new provider request was made.

PASS means no specified defect is found. The verdict is advisory evidence and
does not replace the owner's visual approval.
