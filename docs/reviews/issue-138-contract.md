# Issue #138 v002 blind-review contract

Candidate: the exact commit pinned in `packet.json`.

Review the 4x and native closed/open exports. The RO chat-room screenshot is
the visual authority for the window and closed controls. The museum dropdown
is data authority only. Qwen candidate 1 may contribute only the missing popup
frame and row surface described below.

## Clauses

- **C1 - RO window fidelity.** The candidate retains the RO window's outer
  shadow, white and magenta frame, blue glass title bar, close button,
  body/footer separators, and striped footer while widening the shell to fit
  the required English copy. There are no flat mismatched patches over the
  frame, title gradient, fields, or footer.
- **C2 - Exact mapping.** The title reads `Custom filters`; the body maps to
  `Custom filters:`, `Images per page:` with `20`, `Sort by:` with
  `Relevance`, and `On` / `Off` with On selected. `Pw.` and its field are
  absent. The source button pair remains exact: `OK` and lowercase `cancel`.
- **C3 - Uniform text and spacing.** Every body label, value, radio label, and
  popup option uses the same 40 px PixelMplus size at 4x. The three closed rows
  use equal 84 px baseline gaps. The title alone remains the source-matched
  larger title size. Text has no broken, doubled, clipped, or merged glyphs.
- **C4 - Complete dropdown.** The open state aligns the popup to the left and
  right edges of the sort field and shows all nine Issue strings in order. No
  row, glyph, border, or bottom option is clipped.
- **C5 - Source controls and bounded generation.** Both arrow sprites, both
  radio sprites, and the complete `OK` / `cancel` pair are byte-identical source
  pixels. Qwen candidate 1 supplies only the masked popup frame, selected-row
  treatment, and row surface. Generated glyphs and generated closed-state
  controls do not enter the candidate.
- **C6 - Deterministic evidence.** Relative to the deterministic widened
  source-derived shell, content Assembly changes 146,582 pixels inside a
  312,720-pixel predeclared mask and zero outside it. Because the source and
  candidate widths differ, this is not an ADR 0002 strict exact-preservation
  claim. Closed/native size is 336 x 126; open/native size is 336 x 196. The
  retained OpenRouter Qwen pass requested/completed 2/2 images with zero
  ambiguity and v002 made no new paid request.

PASS means no specified defect is found. The verdict is advisory evidence and
does not replace the owner's visual approval.
