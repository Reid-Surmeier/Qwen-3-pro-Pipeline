# Issue #138 blind-review contract

Candidate: the exact commit pinned in `packet.json`.

Review both the 4x review exports and native-pixel exports. The RO chat-room
window is the only visual authority. The museum dropdown is data authority
only and must not contribute visible styling or pixels.

## Clauses

- **C1 — RO source ownership.** The candidate preserves the source window's
  272 x 126 crop, outer shadow, white and magenta frame, blue glass title bar,
  close button, body/footer separators, and striped footer outside the five
  declared edit regions. It does not resemble the museum screenshot's modern
  rounded dropdown.
- **C2 — Exact mapping.** The title reads `Custom filters`; the body maps to
  `Custom filters:`, `Images per page:` with `20`, `Sort by:` with
  `Relevance`, and `On` / `Off` with On selected. `Pw.` and its password field
  are absent. `OK` and `Cancel` remain.
- **C3 — Complete dropdown.** The open state shows all nine Issue strings in
  the specified order. No row, glyph, border, or bottom option is clipped.
- **C4 — Legible native lettering.** At native and 4x scale, English text has
  no broken, merged, doubled, truncated, or unintelligible glyphs. The
  repository-pinned PixelMplus font is used at its intended 10-pixel grid for
  body copy.
- **C5 — Source control reuse.** The two dropdown buttons exactly reuse the
  source arrow sprite. The On and Off controls exactly reuse the source
  selected and unselected radio sprites. No generated control raster enters
  the final Assembly.
- **C6 — Deterministic evidence.** The closed candidate has 14,811 changed
  native pixels inside a 19,649-pixel permitted-region mask created from five
  fixed edit boxes before composition. The separately computed actual mask is
  a subset, and zero pixels change outside the permitted regions. The open
  state is 272 x 196. The Qwen Render Pass requested and
  completed two images with zero ambiguity; those images are diagnostic only.

PASS means no specified defect is found. The verdict is advisory evidence and
does not replace the owner's visual approval.
