# Issue #138 v004 blind-review contract

Candidate: the exact commit pinned in `packet.json`.

Review the 4x and native closed/open exports. The RO chat-room screenshot is
the visual authority for the window and closed controls. The museum dropdown
is data authority only. Qwen candidate 1 may contribute only the missing popup
frame and row surface described below.

## Clauses

- **C1 - RO window fidelity.** The candidate retains the RO window's inner
  white and magenta frame, blue glass title bar, close button, body/footer
  separators, and striped footer while widening the shell at native
  resolution. The noisy screenshot exterior is replaced by a clean native
  silhouette. There are no resampling halos or flat mismatched patches over
  the title gradient, fields, or footer.
- **C2 - Exact mapping.** The title reads `Custom filters`; the body maps to
  `Custom filters:`, `Images per page:` with `20`, `Sort by:` with
  `Relevance`, and `On` / `Off` with On selected. `Pw.` and its field are
  absent. The source button pair remains exact: `OK` and lowercase `cancel`.
- **C3 - Uniform text and spacing.** Every body label, value, radio label, and
  popup option is drawn at the same native 10 px PixelMplus size. The three
  closed rows use equal 21 px baseline gaps. The 4x review text is an exact
  nearest-neighbor enlargement; the title alone uses the dedicated native
  PixelMplus12 face. Body text reproduces the source's gray `(2,2)` and light
  blue `(1,1)` depth pixels behind its navy strokes. The title reproduces the
  owner crop's gray `(1,1)` depth and light `(-1,-1)` highlight behind black
  strokes. Text has no flat, broken, clipped, or merged glyphs.
- **C4 - Complete dropdown.** The open state aligns the popup to the left and
  right edges of the sort field and shows all nine Issue strings in order. No
  row, glyph, border, or bottom option is clipped.
- **C5 - Source controls and bounded generation.** The review exports restore
  byte-identical full-resolution source crops for the close control, both
  arrows, both radios, and the complete `OK` / `cancel` pair. Qwen candidate 1
  supplies only the masked popup frame, selected-row treatment, and row
  surface. Generated glyphs and generated closed-state controls do not enter
  the candidate.
- **C6 - Deterministic evidence.** Relative to the deterministic native widened
  shell, content Assembly changes only pixels inside its predeclared native
  mask and zero outside it. Because the source and candidate widths differ,
  this is not an ADR 0002 strict exact-preservation claim. Closed/native size
  is 336 x 126; open/native size is 336 x 196. The
  retained OpenRouter Qwen pass requested/completed 2/2 images with zero
  ambiguity and v004 made no new paid request. The open popup also has its own
  declared native mask against the closed candidate on a transparent 336 x 196
  canvas, with zero changes outside the popup rectangle.

PASS means no specified defect is found. The verdict is advisory evidence and
does not replace the owner's visual approval.
