# Custom filters RO window

Issue: [#138](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/138)

## Current candidate

The v002 candidate is a 336 x 126 native-pixel closed Assembly plus a 336 x 196
open-dropdown export. It supersedes the rejected v001 attempt without deleting
that history. The RO chat-room window supplies the frame, shadow, pink border,
glass title bar, field bevels, radio controls, dropdown arrows, footer, and the
entire `OK` / lowercase `cancel` button pair. The museum screenshot supplies
only the nine sort-option strings and their order.

The mapping is:

- `Tpc.` becomes `Custom filters:`.
- `Ppl.` becomes `Images per page:` with value `20`.
- `Room` becomes `Sort by:` with `Relevance` selected.
- `Sec.` becomes `On` / `Off`, with `On` selected.
- `Pw.` and its field are removed.

The open state contains these options exactly:

1. Relevance
2. Title (a-z)
3. Title (z-a)
4. Date (newest-oldest)
5. Date (oldest-newest)
6. Artist/Maker (a-z)
7. Artist/Maker (z-a)
8. Accession Number (0-9)
9. Accession Number (9-0)

## Render Pass

One OpenRouter submission requested two Qwen candidates. Both completed. The
closed state uses none of their pixels; the open state uses only a masked popup
surface from candidate 1.

| Field | Value |
| --- | --- |
| Provider | `openrouter` |
| Model | `qwen/qwen-image-3-pro` |
| Prompt ID | `e12f195d-dfaa-4810-bac9-96963b4b3c35` |
| Requested / completed / ambiguous | `2 / 2 / 0` |
| Seed | `20260903` |
| Estimated cost | `$0.10` |
| Actual cost | Not exposed by ComfyUI history |

The two raw candidates are preserved under
`artifacts/runs/custom-filters-ro-render-v001/`. Candidate 1 was the more
coherent compact layout. V002 imports only its popup frame and row surface
through a glyph-free mask. It imports no generated lettering or generated
closed-state control pixels. No new paid request was made for v002.

## Assembly and fidelity check

`scripts/assemble_custom_filters_ro_v002.py` works at the source's full 4x
review resolution, widens the shell horizontally, and then exports a 336 x 126
native view. Existing arrows, radio sprites, close control, and the complete
button pair are copied at their original full-resolution dimensions. Field
middles use horizontal source-pixel nine-slicing; they are not flat replacement
rectangles.

The page and sort controls reuse the source dropdown-arrow sprite exactly. The
On and Off controls reuse the source selected and unselected radio sprites
exactly. All body labels, values, radio labels, and all nine popup options use
one 40 px PixelMplus size at review resolution, equivalent to its native
10-pixel grid. The three closed-state baselines have equal 84 px gaps. The
title remains the source-matched larger title size. The pinned file is
`godot/fonts/PixelMplus10-Regular.ttf`, SHA-256
`01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7`.

The open popup is aligned to the widened sort field. A hash-locked crop from
Qwen candidate 1 supplies its frame, selected-row treatment, and subtle row
surface. Assembly samples only a donor strip to the right of all generated
glyphs, extends that surface under the mask, and draws the exact nine strings
deterministically at the same 40 px size.

Machine verification records:

- the permitted-region mask is created from the five fixed edit boxes before
  content composition on the deterministic widened shell, and the separately
  computed actual-difference mask is its subset;
- zero content-assembly changes outside that predeclared mask relative to the
  widened shell;
- both native dimensions and all exact strings are frozen by tests;
- source arrows, radio sprites, and the `OK` / `cancel` pair are byte-identical;
- the password field is removed from the source layout;
- the 336 x 196 open canvas contains the entire dropdown, including all nine
  options below the closed window's edge.

Because the canvas is widened from 272 to 336 native pixels, this run is not an
ADR 0002 exact-preservation claim against the differently sized source image.
The mask result covers content edits after deterministic source extension.
Byte-exact claims are limited to the named arrows, radios, and button pair.

## Outputs

- `artifacts/runs/custom-filters-ro-assembly-v002/custom-filters-closed-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/custom-filters-closed.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/custom-filters-open-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/custom-filters-open.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/contact-sheet.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/permitted-edit-mask-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/actual-difference-mask-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v002/verification.json`

## Verification boundary

The automated checks establish deterministic source extension, exact named
sprite reuse, copy, dimensions, option order, and content-mask containment.
They do not constitute human visual approval. The owner still decides whether
the spacing, lettering, and overall RO-style match are accepted.
