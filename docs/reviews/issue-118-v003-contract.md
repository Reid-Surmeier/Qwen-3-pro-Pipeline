# Issue #118 Assembly v003 blind-review contract

Candidate: the exact commit pinned in `packet.json`.

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
- **C3 — Shape-aware Assembly.** Before composition, the edit mask is declared
  from Assembly v001's old exact-ink glyph pixels and the pinned font's new
  glyph silhouettes. It contains no solid enclosing rectangle; the actual RGB
  changed-pixel mask must be a subset. Every per-box fill fraction is at most
  0.37.
- **C4 — Exact and legible copy.** All 19 strings in `run.json` are present
  character-for-character. At full and native scale the text is readable and
  has no visibly broken, merged, doubled, clipped, or haloed glyphs and no
  mismatched white/pink background patch around it.
- **C5 — Tabs.** `object` remains the active upper tab and `material` remains
  the inactive lower tab. Assembly v001's tab silhouettes, fills, stepped
  inactive notch, edges, positions, and orientation are retained; only their
  foreground glyph pixels change.
- **C6 — Deterministic evidence.** The right header controls are byte-identical
  to Assembly v001. The candidate has 4,207 changed native pixels inside a
  predeclared 4,831-pixel native mask, zero changed pixels outside that mask,
  and zero maximum outside-mask channel error. The English strings come from
  repository-pinned PixelMplus fonts, not a generated raster. No new provider
  request was made.

PASS means no specified defect is found. The verdict is advisory evidence and
does not replace the owner's visual approval.
