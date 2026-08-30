# Custom filters RO window

Issue: [#138](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/138)

## Result

The final deliverable is a deterministic 272 x 126 native-pixel Assembly with
closed and open-dropdown review exports. The RO chat-room window owns the
frame, shadow, pink border, glass title bar, field bevels, radio controls,
dropdown arrow, spacing, and footer. The museum screenshot supplies only the
nine sort-option strings and their order; none of its pixels or styling enter
the Assembly.

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

One OpenRouter submission requested two Qwen candidates. Both completed, and
neither is the final output. They were used as layout diagnostics before the
source-owned Assembly was built.

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
coherent compact layout; candidate 2 misplaced the sort control and left too
much empty space. Deterministic Assembly corrected both rather than importing
either generated window.

## Assembly and fidelity check

`scripts/assemble_custom_filters_ro.py` first reduces the style source to its
native 272 x 126 grid with nearest-neighbour sampling. It reconstructs only
five declared regions: title, three body rows, and buttons. The outer frame,
shadow, magenta edge, title-bar glass outside the title, body/footer separators,
and all other unmarked pixels remain source pixels.

The page and sort controls reuse the source dropdown-arrow sprite exactly. The
On and Off controls reuse the source selected and unselected radio sprites
exactly. English copy uses the repository-pinned PixelMplus font at its native
10-pixel grid so glyphs do not collapse at the unsupported 8-pixel size used in
the rejected first Assembly render.

Machine verification records:

- the permitted-region mask is created from the five fixed edit boxes before
  composition, and the separately computed actual-difference mask is its
  subset;
- zero changed pixels outside that predeclared permitted-region mask;
- both native dimensions and all exact strings are frozen by tests;
- the password field differs from and is removed from the source;
- the 272 x 196 open canvas contains the entire dropdown, including all nine
  options below the closed window's edge.

## Outputs

- `artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-closed-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-closed.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-open-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-open.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/contact-sheet.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/edit-mask-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/actual-difference-mask-native.png`
- `artifacts/runs/custom-filters-ro-assembly-v001/verification.json`

## Verification boundary

The automated checks establish source ownership, copy, dimensions, control
reuse, option order, and mask containment. They do not constitute human visual
approval. The owner still decides whether the spacing, lettering, and overall
RO-style match are accepted.
