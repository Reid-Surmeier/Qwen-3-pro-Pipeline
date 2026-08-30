# Custom filters RO window

Issue: [#138](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/138)

## Current candidate

The v003 candidate is a 336 x 126 native-pixel closed Assembly plus a 336 x 196
open-dropdown export. It supersedes rejected v001 and v002 without deleting
their history. All replacement text is rendered once on the native pixel grid;
the RO source supplies the inner frame, title glass, field bevels, control
sprites, footer, and the entire `OK` / lowercase `cancel` pair. The museum
screenshot supplies only the nine sort-option strings and their order.

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
coherent compact layout. V003 imports only its popup frame and row surface
through a glyph-free mask. It imports no generated lettering or generated
closed-state control pixels. No new paid request was made for v003.

## Assembly and fidelity check

`scripts/assemble_custom_filters_ro_v003.py` first reduces the complete 1088 x
504 style source once to its 272 x 126 pixel grid with nearest-neighbor
sampling. It then widens the shell at native resolution with exact source
halves and a bounded center donor strip, and composes the replacement UI at 336
x 126. The widening step never horizontally stretches or LANCZOS-resamples the
complete screenshot. The noisy outer screenshot shadow is replaced by a clean
native rounded silhouette while the inner frame caps remain exact source
pixels.

All body labels, values, radio labels, and all nine popup options use one 10 px
PixelMplus size at native resolution. The three closed-state baselines have
equal 21 px gaps. Their 4x review pixels come only from nearest-neighbor
enlargement, so no independently hinted 40 px glyphs enter the output. The
title remains the source-matched larger native size. The pinned file is
`godot/fonts/PixelMplus10-Regular.ttf`, SHA-256
`01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7`.

After native enlargement, the review exports restore byte-exact
full-resolution source crops for the close control, both arrows, both radios,
and the complete `OK` / `cancel` pair. This retains the source detail that would
otherwise be lost by native downsampling while leaving all replacement text on
the single native grid.

The open popup is aligned to the widened sort field. A hash-locked crop from
Qwen candidate 1 supplies its frame, selected-row treatment, and subtle row
surface. Assembly samples only a donor strip to the right of all generated
glyphs, extends that surface under the mask, and draws the exact nine strings
deterministically at the same native 10 px size.

Machine verification records:

- the native edit mask is created before content composition on the
  deterministic widened shell, and the separately
  computed actual-difference mask is its subset;
- zero content-assembly changes outside that predeclared mask relative to the
  widened shell;
- both native dimensions and all exact strings are frozen by tests;
- inner frame caps plus native controls are exact source pixels, and the review
  controls are byte-identical full-resolution source crops;
- the actual closed and open review exports differ from nearest-neighbor native
  enlargement only inside the named full-resolution source-control overlays;
- the password field is removed from the source layout;
- the popup edges align with the sort field and every measured option-text
  bound, including the ninth option, stays inside the 336 x 196 open canvas.

Because the canvas is widened from 272 to 336 native pixels, this run is not an
ADR 0002 exact-preservation claim against the differently sized source image.
The mask result covers content edits after deterministic source extension.
Byte-exact claims are limited to the named arrows, radios, and button pair.

## Outputs

- `artifacts/runs/custom-filters-ro-assembly-v003/custom-filters-closed-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/custom-filters-closed.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/custom-filters-open-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/custom-filters-open.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/contact-sheet.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/native-edit-mask.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/actual-difference-mask-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v003/verification.json`

## Verification boundary

The automated checks establish deterministic source extension, exact named
sprite reuse, copy, dimensions, option order, and content-mask containment.
They do not constitute human visual approval. The owner still decides whether
the spacing, lettering, and overall RO-style match are accepted.
